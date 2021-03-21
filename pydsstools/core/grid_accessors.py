import logging
from contextlib import contextmanager 
from .._lib import BoundingBox
from .._lib import check_shg_gridinfo,correct_shg_gridinfo,lower_left_xy_from_transform
from .transform import Affine, from_bounds, from_origin
from .accessors import register_grid_accessor
from .grid import _SpatialGridStruct

try:
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.profiles import DefaultGTiffProfile
    from rasterio.crs import CRS
    from rasterio.plot import show as _show # matplotlib?
    from rasterio import mask as riomask
    from osgeo import gdal
    gdal.UseExceptions()
    from osgeo import ogr
    import numpy as np
except:
    logging.debug('Missing rasterio library ...')
    logging.debug('Raster accessor for spatial grid not available.')
else:
    logging.info('Registering raster accessor for SpatialGridStruct')
    @register_grid_accessor("raster")
    class RasterAccessor:
        def __init__(self, grid_struct):
            self._obj = grid_struct
            
        def _default_rasterio_profile(self):
            # prepare rasterio profile
            row = self._obj.height
            col = self._obj.width
            gridinfo = self._obj.profile
            profile = DefaultGTiffProfile(count = 1)
            if row < 256 or col < 256:
                profile.pop('blockxsize')
                profile.pop('blockysize')
            profile['transform'] = gridinfo['grid_transform']
            # TODO: select float32 and float64 based on grid dtype
            profile['dtype'] = 'float32'
            profile['nodata'] = self._obj.nodata
            profile['height'] = row
            profile['width'] = col
            # crs preference
            # 1. User defined
            # 2. grid_crs
            if self._obj._crs:
                logging.debug('Using CRS defined externally for the grid raster')
                profile['crs'] = self._obj._crs
            else:
               crs = self.validate_crs(gridinfo['grid_crs'])
               profile['crs'] = crs.to_wkt()
            return profile

        def _data(self):
            buf = self._obj.read()
            data = buf._data
            return data

        def _as_gdal_datasource(self):
            # create in-memory gdal raster source
            prof = self._default_rasterio_profile()
            driver = gdal.GetDriverByName('MEM')
            ds = driver.Create('',self._obj.width,self._obj.height,1,6) # GDT_Float32 = 6
            ds.SetProjection(prof['crs']) # WKT
            ds.SetGeoTransform(Affine.to_gdal(prof['transform']))
            srcband = ds.GetRasterBand(1)
            srcband.WriteArray(self._data())
            return ds

        def _as_rasterio_datasource(self):
            # create in-memory rasterio datasource compatible with gdal
            from rasterio._io import InMemoryRaster
            prof = self._default_rasterio_profile()
            ds = InMemoryRaster(self._data(),transform = prof['transform'], crs = prof['crs'])
            return ds

        def _as_rasterio_dataset(self):
            # create in-memory rasterio dataset
            prof = self._default_rasterio_profile()
            memfile =  rasterio.MemoryFile()
            with memfile.open(**prof) as ds:
                ds.write(self._data(),1)
            ds = memfile.open()
            return ds

        def _resample(self, out_transform = None, method = Resampling.bilinear, memory = 64):
            # private method 
            # returns resampled array data based
            # default resampling method is bilinear
            prof = self._default_rasterio_profile()
            out_data = np.empty((prof['height'],prof['width']),np.float32)
            # TODO: Compare out_transform with grid's transform
            # returns grid's buffer skipping reprojection if they are equal
            # raise exception if they do not have common space
            reproject(self._data(), out_data,
                      src_nodata = prof['nodata'],
                      dst_nodata = prof['nodata'],
                      src_transform = prof['transform'],
                      dst_transform = out_transform,
                      src_crs = prof['crs'],
                      dst_crs = prof['crs'],
                      resampling = method,
                      warp_mem_limit = memory)
            return out_data

        def validate_crs(self,crs):
            try:
                # this handles crs as epsg code string and integer
                crs = int(crs)
            except:
                pass

            if isinstance(crs,int):
                crs = CRS.from_epsg(crs)
            else:
                crs = CRS.from_string(crs)
            return crs

        def define_crs(self,crs):
            ''' Define crs once for the grid. This crs overides grid_crs during raster analysis. 
            '''
            _crs = self.validate_crs(crs)
            # crs as WKT
            self._obj._crs = _crs.to_wkt()

        def save_tiff(self, filepath, update_profile = None):
            # Use _as_gdal_datasource function for this? 
            # grid_crs in grid dataset is optional and can't be relied upon
            data = self._data()
            # prepare rasterio profile
            profile = self._default_rasterio_profile()

            if isinstance(update_profile,(dict,DefaultGTiffProfile)):
                for k in update_profile:
                    profile[k] = update_profile[k]

                if 'crs' in update_profile:
                    _crs = self.validate_crs(profile['crs']) 
                    profile['crs'] = _crs.to_wkt() 

            with rasterio.open(filepath,'w', **profile) as dst:
                dst.write(data,1)

        def plot(self,**kwargs):
            ''' Display raster plot 
            '''
            mask_zeros = kwargs.pop('mask_zeros',False) # treat zero as nodata
            colorbar = kwargs.pop('colorbar',True) # flag for showing colorbar
            cmap = kwargs.get('cmap','Spectral') # matplotlib colormap
            kwargs['cmap'] = cmap
            ds = self._as_rasterio_dataset()
            buf = ds.read(masked = True)[0]
            mask = buf.mask
            data = buf._data.copy()
            trans = ds.transform
            data[mask] = np.nan
            if mask_zeros: data[data == 0] = np.nan
            if 'ax' in kwargs or not colorbar:
                _show(data,transform=trans,**kwargs)
            else:
                import matplotlib.pyplot as plt
                fig,ax = plt.subplots()
                image = ax.imshow(data,cmap=cmap) # hidden just for colorbar
                _show(data,transform=trans,ax=ax,**kwargs)
                fig.colorbar(image,ax=ax,label=self._obj.profile['data_units'])
                plt.show()

        def generate_contours(self,shape_file,**kwargs):
            ''' Generate contour shapefile using GDALContourGenerate

            Parameters
            -----------
                shape_file: str
                            path of output contour shapefile

                base: float, default 0 
                      base relative to which contour intervals are generated

                interval: float, default 10
                          elevation interval between generated contours

                fixed_levels: list, default []
                              List of elevations at which additional
                              contours are generated

                ignore_nodata: bool, default True
                               flag to ignore nodata pixel during contour generation
            '''
            interval = kwargs.get('interval', 10)
            base = kwargs.get('base', 0)
            fixed_levels = kwargs.get('fixed_levels', [])
            ignore_nodata = kwargs.get('ignore_nodata', True)
            # grid profile
            prof = self._default_rasterio_profile()
            # create in-memory gdal raster source
            ds1 = self._as_gdal_datasource()
            srcband = ds1.GetRasterBand(1)
            # create contour shape file
            crs = ogr.osr.SpatialReference()
            crs.ImportFromWkt(prof['crs'])
            ds2 = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(shape_file)
            contour_layer = ds2.CreateLayer('contour',crs,ogr.wkbMultiLineString)
            field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
            contour_layer.CreateField(field_defn)
            field_defn = ogr.FieldDefn("ELEV", ogr.OFTReal)
            contour_layer.CreateField(field_defn)
            # contouring method
            use_nodata = 0 if ignore_nodata else 1
            gdal.ContourGenerate(srcband,interval,base,         # interval, base
                                 fixed_levels,                  # fixedlevelcount list
                                 use_nodata, prof['nodata'] ,   # usenodata, nodata
                                 contour_layer,                 # dstlayer 
                                 0,1)                           # ID field, ELEV field

        def mask(self, poly, all_touched=False, invert=False, filled=True, crop=False,
                 pad=False, pad_width=0.5):
            ''' Creates a masked or filled array using input shapes conforming
                to __geo_interface__ protocal. It functions same as 
                rasterio.mask.mask. Cells are masked or set to nodata outside the
                input shapes unless invert is True.

                Parameters
                ----------
                    poly: string, list or shape
                          Shapefile path, any geomtric shape, list of shapes, or bounding box
                    See rasterio.mask.mask documentation for other parameters.
                    https://rasterio.readthedocs.io/en/latest/api/rasterio.mask.html

                Returns
                -------
                    out_data: numpy 2D array
                              Masked array data
                    out_transform: affine object
                              Affine transform of output data   
            '''
            shapes = guard_vector_mask(poly)
            if not isinstance(shapes,(list,tuple)):
                shapes = [shapes]
            logging.debug('Raster mask shapes = %r',shapes)
            ds = self._as_rasterio_dataset()
            out_data, out_transform = riomask.mask(ds, shapes, 
                                                   all_touched = all_touched,
                                                   invert = invert,
                                                   filled = filled,
                                                   crop = crop,
                                                   pad = pad,
                                                   pad_width = pad_width)
            out_data = np.ma.masked_values(out_data,ds.nodata)
            #Wrap the output with SpatialGridStruct like container
            gridinfo = self._obj.profile
            gridinfo['grid_transform'] = out_transform
            gridinfo['transform'] = out_transform # remove this after grid.pyx fix
            logging.debug('masked out transform = %r',out_transform)
            prof = self._default_rasterio_profile()
            gridinfo['grid_crs'] = prof['crs']
            if gridinfo['grid_type'].lower() in ('albers','albers-time','shg','shg-time'):
                gridinfo = correct_shg_gridinfo(gridinfo,out_data[0].shape)
            st = _SpatialGridStruct(out_data[0],gridinfo)
            return st               

    class VectorShape(object):
        def __init__(self,shell,holes=None):
            if not isinstance(shell, (list,tuple)):
                raise Exception('Argument must a list or tuple')
            self.coords = []
            self.coords.append(tuple(shell))
            if holes:
                self.coords.extend(tuple(holes))

        @property
        def __geo_interface__(self):
            return {'type': 'Polygon',
                    'coordinates': self.coords}

        @classmethod
        def from_bounds(cls, xmin, ymin, xmax, ymax):
            return cls([
                (xmin, ymin),
                (xmin, ymax),
                (xmax, ymax),
                (xmax, ymin),
                (xmin, ymin)])

    def guard_vector_mask(feat):
        ''' Transform feat to polygon feature if does not have __geo_interface__ attribute'''
        attr = getattr(feat,'__geo_interface__',None)
        if not attr is None:
            return feat
        elif isinstance(feat, str):
            return shapefile_to_shapes(feat) 
        elif isinstance(feat, ogr.Feature):
            return feat.ExportToJson()
        elif isinstance(feat,BoundingBox):
            return VectorShape.from_bounds(feat.left,feat.bottom,feat.right,feat.top)
        elif isinstance(feat,(list,tuple)):
            if len(feat) > 0:
                attr = getattr(feat[0],'__geo_interface__',None)
                if not attr is None:
                    # list of shapely like shapes
                    return feat
                elif isinstance(feat[0],(list,tuple)):
                    # list of coordinates for polygon
                    return VectorShape(*feat)
                else:
                    raise Exception('Invalid shape list provided')
            else:
                raise Exception('Empty shape list provided')
        else:
            raise Exception('Invalid shape data')

    def shapefile_to_shapes(shape_file):
        ds = ogr.Open(shape_file)
        lyr = ds.GetLayer(0)
        shapes = []
        for feat in lyr:
            shape = guard_vector_mask(feat)
            shapes.append(shape)
        return shapes

