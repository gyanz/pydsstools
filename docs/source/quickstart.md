# Quickstart

## Opening a DSS file
Import Open class from pydsstools
```{code-block} python

from pydsstools.heclib.dss.Heclib import Open
```

Open file in read and write mode (default behavior)
```{code-block} python

fid = Open("example.dss")
```

Open file in read mode 
```{code-block} python

fid = Open("example.dss",mode="r")
```

Create new DSS version 7 file  
```{code-block} python

fid = Open("newfile.dss")
```

Create new DSS version 6 file  
```{code-block} python

fid = Open("newfile.dss", version=6)
```

## TimeSeries data

### Regular TimeSeries
#### Reading Regular TimeSeries
#### Writing Regular TimeSeries

### IRegular TimeSeries
#### Reading Iregular TimeSeries
#### Writing Iregular TimeSeries

## Paired data

## Gridded data