Reference File Types
====================
The reset correction step uses a RESET reference file.

.. include:: ../includes/standard_keywords.rst

RESET Reference File Format
---------------------------
The reset reference files are FITS files with 3 IMAGE extensions and 1 BINTABLE
extension. The FITS primary data array is assumed to be empty. The 
characteristics of the three image extension are as follows:

=======  =====  ============================== =========
EXTNAME  NAXIS  Dimensions                     Data type
=======  =====  ============================== =========
SCI      4      ncols x nrows x ngroups x nint float
ERR      4      ncols x nrows x ngroups x nint float
DQ       2      ncols x nrows                  integer
=======  =====  ============================== =========

.. include:: ../includes/dq_def.rst

The SCI and ERR data arrays are 4-D, with dimensions of ncols x nrows x 
ngroups X nints, where ncols x nrows matches the dimensions of the raw detector
readout mode for which the reset applies. The reference file contains the 
number of NGroups planes required for the correction to be zero on
the last plane Ngroups plane.  The correction for the first few
integrations varies and eventually settles down to a constant correction
independent of integration number.  
