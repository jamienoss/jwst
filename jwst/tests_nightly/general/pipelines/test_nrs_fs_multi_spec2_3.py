import pytest
from astropy.io import fits
from jwst.pipeline.calwebb_spec2 import Spec2Pipeline

pytestmark = [
    pytest.mark.usefixtures('_jail'),
    pytest.mark.skipif(not pytest.config.getoption('bigdata'),
                       reason='requires --bigdata')
]

def test_nrs_fs_multi_spec2_3(_bigdata):
    """
    Regression test of calwebb_spec2 pipeline performed on NIRSpec fixed-slit data
    using the ALLSLITS subarray and detector NRS2.
    """
    step = Spec2Pipeline()
    step.save_bsub = True
    step.save_results = True
    step.resample_spec.save_results = True
    step.cube_build.save_results = True
    step.extract_1d.save_results = True
    step.run(_bigdata+'/pipelines/jw84600002001_02101_00001_nrs2_rate.fits')

    ignore_keywords = ['DATE','CAL_VER','CAL_VCS','CRDS_VER','CRDS_CTX']

    na = 'jw84600002001_02101_00001_nrs2_cal.fits'
    nb = _bigdata+'/pipelines/jw84600002001_02101_00001_nrs2_cal_ref.fits'
    h = fits.open(na)
    href = fits.open(nb)
    result = fits.diff.FITSDiff(h,
                              href,
                              ignore_hdus=['ASDF'],
                              ignore_keywords=ignore_keywords,
                              rtol = 0.00001)
    assert result.identical, result.report()

    na = 'jw84600002001_02101_00001_nrs2_s2d.fits'
    nb = _bigdata+'/pipelines/jw84600002001_02101_00001_nrs2_s2d_ref.fits'
    h = fits.open(na)
    href = fits.open(nb)
    result = fits.diff.FITSDiff(h,
                              href,
                              ignore_hdus=['ASDF'],
                              ignore_keywords=ignore_keywords,
                              rtol = 0.00001)
    assert result.identical, result.report()

    na = 'jw84600002001_02101_00001_nrs2_x1d.fits'
    nb = _bigdata+'/pipelines/jw84600002001_02101_00001_nrs2_x1d_ref.fits'
    h = fits.open(na)
    href = fits.open(nb)
    result = fits.diff.FITSDiff(h,
                              href,
                              ignore_hdus=['ASDF'],
                              ignore_keywords=ignore_keywords,
                              rtol = 0.00001)
    assert result.identical, result.report()
