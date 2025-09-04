About pydsstools
===

pydsstools is a Cython based Python library to manipulate [HEC-DSS](http://www.hec.usace.army.mil/software/hec-dssvue/) database file. It supports regular/irregular time-series, paired data series and spatial grid records. It is compatible with 64-bit Python on Windows 10 and Ubuntu like linux distributions. For the later, zlib, math, quadmath, and gfortran libraries must be installed. [dssvue](https://github.com/gyanz/dssvue) python library provides graphical user interface for HEC-DSS. There is also a Rust binding [hecdss](https://github.com/gyanz/hecdss-rs) for HEC-DSS.    

About HEC-DSS <sup>[1]</sup>
===

HEC-DSS is designed to be optimal for storing and retrieving large sets, or series, of data. HEC-DSS is not a relational database, but a database that is designed to retrieve and store large amounts of data quickly that are not necessarily interlinked to other sets of data, like relational databases are. Additionally, HEC-DSS provides a flexible set of utility programs and is easy to add to a user's application program. These are the features that distinguish HEC-DSS from most commercial relational database programs and make it optimal for scientific applications.

HEC-DSS uses a block of sequential data as the basic unit of storage. Each block contains a series of values of a single variable over a time span appropriate for most applications. The basic concept underlying HEC-DSS is the organization of data into records of continuous, applications-related elements as opposed to individually addressable data items. This approach is more efficient for scientific applications than a relational database system because it avoids the processing and storage overhead required to assemble an equivalent record from a relational database.

Data is stored in blocks, or records, within a file and each record is identified by a unique name called a "pathname." Each time data is stored or retrieved from the file, its pathname is used to access its data. Information about the record (e.g., units) is stored in a "header array." This includes the name of the program writing the data, the number of times the data has been written to, and the last written date and time. HEC-DSS documents stored data completely via information contained in the pathname and stored in the header so no additional information is required to identify it. One data set is not directly related to another so there is no need to update other areas of the database when a new data set is stored. The self-documenting nature of the database allows information to be recognized and understood months or years after it was stored.

Because of the self-documenting nature of the pathname and the conventions adopted, there is no need for a data dictionary or data definition file as required with other database systems. In fact, there are no database creation tasks or any database setup. Both HEC-DSS utility programs and applications that use HEC-DSS will generate and configure HEC-DSS database files automatically. There is also no pre-allocation of space; the software automatically expands the file size as needed.

HEC-DSS references data sets, or records, by their pathnames. A pathname may consist of up to 391 characters and is, by convention, separated into six parts, which may be up to 64 characters each. Each part is delimited by a slashe "/", and is labeled "A" through "F", as follows: /A/B/C/D/E/F/.

A list of the pathnames in a DSS file is called a "catalog." In version 6, the catalog was a separate file; in version 7, the catalog is constructed directly from pathnames in the file.

Multi-user access mode is handled automatically by HEC-DSS. The user does not need to do anything to turn it on. Multi-user access allows multiple users, multiple processes, to read and write to the same HEC-DSS file at the same time. This is true for a network drive as well as a local drive. You can have a shared network HEC-DSS file that has several processes reading and writing to it at the same time. The only drawback is that file access may be slower, depending on the operating system.

 1. USACE, Hydrologic Engineering Center (July, 2019). HEC Data Storage System Guide (Draft).

Changes
===

[**changelog**][changelog]

   [changelog]: https://github.com/gyanz/pydsstools/blob/master/CHANGES.MD

Documentation
===

📖 The full documentation (generated with Sphinx) will be published soon.  
In the meantime, please refer to the [examples](pydsstools/examples) and the [changelog](CHANGES.MD) for usage details and updates.

Dependencies
===

- [NumPy](https://www.numpy.org)
- [pandas](https://pandas.pydata.org/)
- [affine](https://pypi.org/project/affine/)
- [MS Visual C++ Redistributable for VS 2015 - 2019](https://aka.ms/vs/16/release/vc_redist.x64.exe)

Build from source
===
Download the source files, open the command prompt in the root directory, and enter the following command. Note that the command prompt must be setup with build tools and python environment.
```
python -m build 
```

Installation from [PyPI](https://pypi.org/project/pydsstools/)
===
```
pip install pydsstools
```

Contributing
===
All contributions, bug reports, bug fixes, documentation improvements, enhancements and ideas are welcome.
Feel free to ask questions on my [email](mailto:gyanBasyalz@gmail.com).


License
===
This program is a free software: you can modify and/or redistribute it under [MIT](LICENSE) license. 
