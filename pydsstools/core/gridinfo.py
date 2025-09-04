'''

'''
import logging
from math import floor
from enum import Enum,IntEnum
from typing import Any,Tuple,List,Union,Optional,Iterable

try:
    # python 3.10+
    from typing import Annotated,TypeAlias,Literal
except:
    # 3.8 <= python < 3.10
    from typing_extensions import Annotated,TypeAlias,Literal

from pydantic import (Field, AliasChoices,
                      BaseModel,
                      ConfigDict, TypeAdapter,
                      BeforeValidator, AfterValidator,
                      model_validator
)

__all__ = ['GridInfoCreate','GridInfo','HrapInfo','AlbersInfo','SpecifiedInfo',
           'GridType','DataType','CompressionMethod','Datum']
# Using GridInfoCreate is recommended to generate each type of grid

class GridType(IntEnum):
    invalid = -9999
    undefined_time = 400    
    undefined = 401    
    hrap_time = 410    
    hrap = 411    
    albers_time = 420    
    albers = 421    
    specified_time = 430    
    specified = 431
    
class DataType(IntEnum):
    invalid = -9999
    per_aver =  0   
    per_cum =  1   
    inst_val =  2   
    inst_cum =  3   
    freq =  4   

class CompressionMethod(IntEnum):
    invalid = -9999
    undefined = 0
    uncompressed =  1
    zlib = 26
    hec = 101001 # PRECIP_2_BYTE   

class Datum(IntEnum):
    invalid = -9999
    undefined = 0
    nad27 = 1
    nad83 = 2

PairLikeInt: TypeAlias = Union[
    Tuple[int, int],
    Annotated[List[int], Field(min_items=2, max_items=2)]
]

PairLikeFloat: TypeAlias = Union[
    Tuple[float, float],
    Annotated[List[float], Field(min_items=2, max_items=2)]
]

GridTypeField = Field(validation_alias=AliasChoices('grid_type','type','gtype','gridtype','grid'),
)

class _GridInfo7(BaseModel):
    """Base class for GridInfo, HrapInfo, AlbersInfo and SpecifiedInfo
    """
    model_config = ConfigDict(extra='allow',validate_default=True)
    # extra = ignore, allow, forbid

    extra: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode='before')
    @classmethod
    def _bucket_extras(cls, data: Any) -> Any:
        # Only normalize mapping-like inputs
        if not isinstance(data, dict):
            return data

        # Get declared field names without relying on private attributes.
        # Prefer the public mapping if present; fall back to annotations.
        declared = set(getattr(cls, 'model_fields', {}) or getattr(cls, '__annotations__', {}))

        # Separate known vs unknown; keep user's provided 'extra' dict (if any)
        provided_extra = data.get('extra')
        extras = {k: v for k, v in data.items() if k not in declared and k != 'extra'}
        known = {k: v for k, v in data.items() if k in declared}

        # Merge extras (user-supplied extras take precedence)
        merged_extra: dict[str, Any] = {}
        if isinstance(provided_extra, dict):
            merged_extra.update(provided_extra)
        merged_extra.update(extras)

        # Pass only known fields + our consolidated extra to BaseModel
        if merged_extra:
            known['extra'] = merged_extra
        return known

    def __setattr__(self, name: str, value: Any) -> None:
        # Known fields behave normally (validated by Pydantic)
        declared = getattr(self.__class__, 'model_fields', {}) or getattr(self.__class__, '__annotations__', {})
        if name in declared or name == 'extra' or name.startswith('_'):
            return super().__setattr__(name, value)
        # Unknown attributes go into `.extra`
        self.extra[name] = value 
    # standard repr() / str()

    def __repr_args__(self) -> Iterable[Tuple[str, Any]]:
        # show only declared fields 
        for name in self.__pydantic_fields__:
            if name in self.__dict__ and name != "extra":
                yield name, getattr(self, name)

    @property
    def extra_info(self):
        #return self.__pydantic_extra__
        return self.extra
    
    # lower_left_cell indices update
    def update_albers_lower_left_cell_from_minxy(self):
        if self.grid_type == GridType.albers or self.grid_type == GridType.albers_time:
            logging.info('Updating lower left cell indices using mix_xy of Albers GridInfo')
            x_cell0, y_cell0 = self.coords_cell0
            llc = lower_left_cell_from_minxy(self.min_xy,self.shape,self.cell_size,x_cell0,y_cell0)
            self.lower_left_cell = llc

    def update_albers_lower_left_cell_from_transform(self,transform):
        dx = self.cell_size
        dx_t = transform[0]
        if abs(dx - dx_t) > 0.001:
            logging.error('Cell size in gridinfo is different than cell size in the transform')
            logging.error('Skipping computation of lower left cell indices')
            return

        if self.grid_type == GridType.albers or self.grid_type == GridType.albers_time:
            logging.info('Updating lower left cell indices of Albers GridInfo')
            x_cell0, y_cell0 = self.coords_cell0
            if x_cell0 != 0.0 or y_cell0 != 0.0:
                logging.warning('Normally, the grid origin coordinates in SHG/Albers (epsg 5070) grid is (0,0). This is not the case here.')
            llc = lower_left_cell_from_transform(transform,self.shape,x_cell0,y_cell0)
            self.lower_left_cell = llc

    def update_specified_lower_left_cell(self):
        if self.grid_type == GridType.specified or self.grid_type == GridType.specified_time:
            logging.info('Updating lower left cell indices of Specified GridInfo')
            self.lower_left_cell = (0,0)

    # coords_cell0 update
    def update_shg_coords_cell0(self):
        if self.grid_type == GridType.albers or self.grid_type == GridType.albers_time:
            self.coords_cell0 = (0.0,0.0)

    def update_specified_coords_cell0_from_minxy(self):
        if self.grid_type == GridType.specified or self.grid_type == GridType.specified_time:
            self.coords_cell0 = self.min_xy

    def update_specified_coords_cell0_from_transform(self,transform):
        if self.grid_type == GridType.specified or self.grid_type == GridType.specified_time:
            dx = self.cell_size
            dx_t = transform[0]
            if abs(dx - dx_t) > 0.001:
                logging.error('Cell size in gridinfo is different than cell size in the transform')
                logging.error('Skipping computation of coordinates of cell0 of grid located at bottom left corner')
                return

            # xmin and ymin of grid consistent with MetVue
            coords_cell0 = coords_of_cell0_of_specified_grid(transform,self.shape)
            self.lower_left_cell = (0,0)
            self.coords_cell0 = coords_cell0

    def update_from_crs(self):
        # for Albers and Specified
        raise NotImplementedError

    def get_v6_grid_type(self):
        if self.grid_type in [GridType.hrap, GridType.hrap_time]:
            return GridType.hrap_time       
        elif self.grid_type in [GridType.albers, GridType.albers_time]:
            return GridType.albers_time       
        elif self.grid_type in [GridType.specified, GridType.specified_time]:
            return GridType.specified_time       
        else:
            return GridType.undefined_time

    def grid_type_has_time(self):
        if self.grid_type in [GridType.undefined_time,GridType.hrap_time,GridType.albers_time,GridType.specified_time]:
            return True           

class GridInfo(_GridInfo7):
    grid_type:Annotated[
        Literal[GridType.undefined_time,GridType.undefined],
        GridTypeField    
    ] = GridType.undefined_time
    data_units:str = Field(default='', validation_alias=AliasChoices('data_units','du','data_unit'))
    data_type:DataType = Field(validation_alias=AliasChoices('data_type','dt','datatype','dtype'))
    lower_left_cell:Optional[PairLikeInt] = Field(default=None,validation_alias=AliasChoices('lower_left_cell','llc','llci','lower_left_cell_index','lower_cell','ll_cell'))
    shape:Union[Tuple[int,int],Annotated[List[int],Field(min_items=2,max_items=2)]]
    cell_size:float = Field(validation_alias=AliasChoices('cell_size','cellsize','cs','dx','spacing','grid_size'))
    compression_method:CompressionMethod = Field(default=CompressionMethod.zlib, validation_alias=AliasChoices('compression_method','compression','comp'))
    compression_base:float = Field(default=0.0, validation_alias=AliasChoices('compression_base','comp_base','compbase','base','compressionbase'))
    compression_factor:float = Field(default=0.0, validation_alias=AliasChoices('compression_factor','comp_factor','comp_scale','compression_scale','scale'))
    max_val:float = Field(default=0.0, validation_alias=AliasChoices('max_val','max','maximum','max_value','mx','maxima'))
    min_val:float = Field(default=0.0, validation_alias=AliasChoices('min_val','min','minimum','min_value','minima'))
    mean_val:float = Field(default=0.0, validation_alias=AliasChoices('mean_val','mean','mean_value','average','avg'))
    range_vals:Annotated[List[float],Field(min_items=0)] = Field(default_factory=list, validation_alias=AliasChoices('range_vals','rv','range_values','rangevals'))
    range_counts:Annotated[List[int],Field(min_items=0)] = Field(default_factory=list,validation_alias=AliasChoices('range_counts','rc','rangecounts'))
    min_xy:Optional[PairLikeFloat] = Field(default=None, validation_alias=AliasChoices('min_xy','minxy','xy_min','xymin','llxy'))

class HrapInfo(GridInfo):
    grid_type:Annotated[
        Literal[GridType.hrap_time,GridType.hrap],
        GridTypeField    
    ] = GridType.hrap_time
    data_source:str = Field(default='', validation_alias=AliasChoices('data_source','data_sources','data_source','datasource','datasources','dsource','dsources'))

class AlbersInfo(GridInfo):
    grid_type:Annotated[
        Literal[GridType.albers_time,GridType.albers],
        GridTypeField    
    ] = GridType.albers_time
    proj_datum:Datum = Field(default=Datum.nad83, validation_alias=AliasChoices('proj_datum','Datum','datum'))
    proj_units:str = Field(default='meter', validation_alias=AliasChoices('proj_units','pu','proj_unit','projection_unit','projection_units'))
    lat_0:float = Field(default=23.0, validation_alias=AliasChoices('lat_0','lat_origin','lo','latorigin','lat0'))
    lat_1:float = Field(default=29.5, validation_alias=AliasChoices('lat_1','par1','parallel1','lat_1','lat1','first_parallel'))
    lat_2:float = Field(default=49.5, validation_alias=AliasChoices('lat_2','second_parallel','par2','parallel2','sec_parallel','sec_par','lat2'))
    lon_0:float = Field(default=-96.0, validation_alias=AliasChoices('lon_0','cm','cmer','lon_0','lon0','central_meridian'))
    x_0:float = Field(alias='fe',default=0.0, validation_alias=AliasChoices('x_0','x0','fe','false_easting'))
    y_0:float = Field(alias='fn',default=0.0, validation_alias=AliasChoices('y_0','y0','fn','false_northing'))
    # (easting, northing) of southwest corner of cell(0,0) - do not confuse this with coordinates or indices of lower left cell of grid
    # I think it should equal x_0 and y_0 normally in SHG/Albers
    coords_cell0:Optional[PairLikeFloat] = Field(default=None, validation_alias=AliasChoices('coords_cell0','coordscell0','coords0','xy_cell0'))


class SpecifiedInfo(GridInfo):
    grid_type:Annotated[
        Literal[GridType.specified_time,GridType.specified],
        GridTypeField    
    ] = GridType.specified_time
    crs: str = Field(default='', validation_alias=AliasChoices('crs','crs_definition','crs_def','srs','srs_def'))
    crs_name: str = Field(default='', validation_alias=AliasChoices('crs_name','crsname','srsname'))
    nodata: float = Field(allow_inf_nan=True, validation_alias=AliasChoices('nodata','null','nulldata','nullvalue'))
    tzid: str = Field(default='', validation_alias=AliasChoices('tzid','timezoneID','time_zone_id','timezone_id'))
    tzoffset: int = Field(default=0, ge=-24, le=24, validation_alias=AliasChoices('tzoffset','timezoneOffset','timezone_offset','time_zone_offset'))
    coords_cell0:Optional[PairLikeFloat] = Field(default=None, validation_alias=AliasChoices('coords_cell0','coordscell0','coords0','xy_cell0'))
    is_interval: bool = Field(default=True, validation_alias=AliasChoices('is_interval','isinterval','isint'))
    time_stamped: bool = Field(default=True, validation_alias=AliasChoices('time_stamped','is_time_stamped','istimestamped','isstamped'))

#GridInfoUnionType:TypeAlias = Annotated[
GridInfoUnionType = Annotated[
    Union[GridInfo, HrapInfo, AlbersInfo, SpecifiedInfo],
    Field(descriminator='grid_type')
]

def create_gridinfo(**kwargs) -> _GridInfo7:
    if not kwargs:
        raise TypeError('Provide keyword arguments to create GridInfo (e.g., grid_type=GridType.hrap, ...)')
    Adapter = TypeAdapter(GridInfoUnionType)
    return Adapter.validate_python(kwargs)

# ==============================================================================
# Use this to create GridInfo for Undefined, Hrap, Albers and Specified grids
GridInfoCreate = create_gridinfo
# ==============================================================================

def lower_left_cell_from_transform(transform,shape,xcoord_cell0=0,ycoord_cell0=0):
    # https://www.hec.usace.army.mil/confluence/hmsdocs/hmsum/4.8/geographic-information/coordinate-reference-systems    
    # https://rashms.com/blog/standard-hydrologic-grid-shg-in-hec-hms-modeling/
    cellsize_x = transform[0] # don't think this can ever be negative
    xmin = transform[2]
    cellsize_y = transform[4] # negative for north-up
    ymax = transform[5]

    if abs(cellsize_x) != abs(cellsize_y):
        logging.warning('Note that cell sizes in x and y should be same for specified grid stored in HEC-DSS')

    rows = shape[0]
    xmin_easting = xmin - xcoord_cell0
    ymin = ymax + rows * cellsize_y
    ymin_northing = ymin - ycoord_cell0
    lower_left_x = int(floor(xmin_easting/abs(cellsize_x)))
    lower_left_y = int(floor(ymin_northing/abs(cellsize_y)))
    return (lower_left_x,lower_left_y)

def lower_left_cell_from_minxy(minxy,shape,cellsize,xcoord_cell0=0,ycoord_cell0=0):
    rows = shape[0]
    xmin,ymin = minxy
    xmin_easting = xmin - xcoord_cell0
    ymin_northing = ymin - ycoord_cell0
    lower_left_x = int(floor(xmin_easting/cellsize))
    lower_left_y = int(floor(ymin_northing/cellsize))
    return (lower_left_x,lower_left_y)


def coords_of_cell0_of_shg_grid():
    return (0.0,0.0)

def lower_left_cell_of_specified_grid():
    # Source: https://www.hec.usace.army.mil/confluence/metdoc/metum/3.4.0/general-information-and-tips/dss-specifiedgridinfo-in-hec-metvue
    # Here, like MetVue, the lower left cell of the grid is assumed as cell0
    return (0,0)

def coords_of_cell0_of_specified_grid(transform,shape):
    # Note that specified grid can assume any geographical location as origin cell
    # Based on the origin cell assumption, the coordinates of cell0 will change 
    # Here, like MetVue, the lower left cell of the grid is assumed as cell0
    # Thus, the function returns (xmin,ymin) of the grid that is also the coordinates of 
    # south-west corner of cell0.  
    cellsize_x = transform[0] 
    cellsize_y = transform[4]
    xmin = transform[2]
    ymax = transform[5]
    rows = shape[0]

    if abs(cellsize_x) != abs(cellsize_y):
        logging.warning('Note that cell sizes in x and y should be same for specified grid stored in HEC-DSS')

    ymin = ymax + rows * cellsize_y
    return (xmin,ymin)


