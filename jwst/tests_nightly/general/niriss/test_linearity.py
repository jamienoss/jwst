import pytest
from astropy.io import fits
from jwst.linearity.linearity_step import LinearityStep

from ..helpers import add_suffix

pytestmark = [
    pytest.mark.usefixtures('_jail'),
    pytest.mark.skipif(not pytest.config.getoption('bigdata'),
                       reason='requires --bigdata')
]


def test_linearity_niriss(_bigdata):
    """
    Regression test of linearity step performed on NIRISS data.
    """
    suffix = 'linearity'
    output_file_base, output_file = add_suffix('linearity1_output.fits', suffix)

    LinearityStep.call(_bigdata+'/niriss/test_linearity/jw00034001001_01101_00001_NIRISS_dark_current.fits',
                       output_file=output_file_base, suffix=suffix
                       )
    h = fits.open(output_file)
    href = fits.open(_bigdata+'/niriss/test_linearity/jw00034001001_01101_00001_NIRISS_linearity.fits')
    newh = fits.HDUList([h['primary'],h['sci'],h['err'],h['pixeldq'],h['groupdq']])
    newhref = fits.HDUList([href['primary'],href['sci'],href['err'],href['pixeldq'],href['groupdq']])
    result = fits.diff.FITSDiff(newh,
                              newhref,
                              ignore_keywords = ['DATE','CAL_VER','CAL_VCS','CRDS_VER','CRDS_CTX'],
                              rtol = 0.00001
    )
    assert result.identical, result.report()
