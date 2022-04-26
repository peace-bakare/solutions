"""Tests for vma.py."""

import pytest
import io
import pathlib
import tempfile

from model import vma
import numpy as np
import pandas as pd


basedir = pathlib.Path(__file__).parents[2]
datadir = pathlib.Path(__file__).parents[0].joinpath('data')


def test_vals_from_real_soln_csv():
    """ Values from Silvopasture Variable Meta Analysis """
    f = datadir.joinpath('vma1_silvopasture.csv')
    v = vma.VMA(filename=f, low_sd=1.0, high_sd=1.0)
    result = v.avg_high_low()
    expected = (314.15, 450.0, 178.3)
    assert result == pytest.approx(expected)


def test_source_data():
    s = """Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
        Check that this text is present, 0%, %, 0, 0
        """
    f = io.StringIO(s)
    v = vma.VMA(filename=f)
    assert 'Check that this text is present' in v.source_data.to_html()


def test_invalid_discards():
    s = """Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
        a, 10000, ,
        b, 10000, ,
        c, 10000, ,
        d, 10000, ,
        e, 10000, ,
        f, 10000, ,
        g, 10000, ,
        h, 10000, ,
        i, 10000, ,
        j, 10000, ,
        k, 10000, ,
        l, 10000, ,
        m, 10000, ,
        n, 10000, ,
        o, 10000, ,
        p, 20000, ,
        q, 1, ,
    """
    f = io.StringIO(s)
    v = vma.VMA(filename=f, discard_multiplier=1)
    result = v.avg_high_low()
    expected = (10000, 10000, 10000)  # rows p and q should be discarded.
    assert result == pytest.approx(expected)
    f = io.StringIO(s)
    v = vma.VMA(filename=f, discard_multiplier=1, stat_correction=False)
    result = v.avg_high_low()
    assert result != pytest.approx(expected)


def test_no_discards_if_weights():
    """Same test as test_invalid_discards but with weights, so there should be no discards."""
    s = """Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
        a, 10000, , , , 1.0,
        b, 10000, , , , 1.0,
        c, 10000, , , , 1.0,
        d, 10000, , , , 1.0,
        e, 10000, , , , 1.0,
        f, 10000, , , , 1.0,
        g, 10000, , , , 1.0,
        h, 10000, , , , 1.0,
        i, 10000, , , , 1.0,
        j, 10000, , , , 1.0,
        k, 10000, , , , 1.0,
        l, 10000, , , , 1.0,
        m, 10000, , , , 1.0,
        n, 10000, , , , 1.0,
        o, 10000, , , , 1.0,
        p, 10000000000, , , , 1.0,
        q, 1, , , , 1.0,
    """
    f = io.StringIO(s)
    v = vma.VMA(filename=f, low_sd=1.0, high_sd=1.0, use_weight=True)
    result = v.avg_high_low()
    expected = (10000, 10000, 10000)
    assert result != pytest.approx(expected)


def test_excluded_data():
    s = """Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
        a, 10000, , , , 1.0, False
        b, 10000, , , , 1.0, False
        c, 40000, , , , 1.0, True
    """
    f = io.StringIO(s)
    v = vma.VMA(filename=f, low_sd=1.0, high_sd=1.0)
    result = v.avg_high_low()
    expected = (10000, 10000, 10000)  # The 40000 value should be excluded.
    assert result == pytest.approx(expected)


def test_excluded_data_weights_are_incorrect():
    s = """Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
        a, 10000, , , , 0.5, False
        b, 10000, , , , 0.5, False
        c, 40000, , , , 1.0, True
    """
    f = io.StringIO(s)
    v = vma.VMA(filename=f, low_sd=1.0, high_sd=1.0, use_weight=True)
    result = v.avg_high_low()
    # The 40000 value should be excluded, but its weight is included in the Excel implementation.
    # Expected value generated by entering the datapoints from this test into Excel.
    expected = (5000, 9330.127, 669.873)
    # When https://docs.google.com/document/d/19sq88J_PXY-y_EnqbSJDl0v9CdJArOdFLatNNUFhjEA/edit#heading=h.qkdzs364y2t2
    # handling is removed this test will fail. It should be removed at that point, as it no longer
    # serves a purpose.
    assert result == pytest.approx(expected)


def test_single_study():
    f = io.StringIO("""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 39%, %,
      """)
    v = vma.VMA(filename=f)
    result = v.avg_high_low()
    expected = (0.39, 0.39, 0.39)
    assert result == pytest.approx(expected)


def test_missing_columns():
    f = io.StringIO("""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 1000
      """)
    v = vma.VMA(filename=f)
    result = v.avg_high_low()
    expected = (1000, 1000, 1000)
    assert result == pytest.approx(expected)


def test_avg_high_low_key():
    f = datadir.joinpath('vma1_silvopasture.csv')
    v = vma.VMA(filename=f, low_sd=1.0, high_sd=1.0)
    avg = v.avg_high_low(key='mean')
    assert avg == pytest.approx(314.15)
    low = v.avg_high_low(key='low')
    assert low == pytest.approx(178.3)
    with pytest.raises(ValueError):
        v.avg_high_low(key='not a key')


def test_avg_high_low_exclude():
    f = datadir.joinpath('vma21_silvopasture.csv')
    v = vma.VMA(filename=f, low_sd=1.0, high_sd=1.0)
    assert v.avg_high_low()[0] == pytest.approx(4.64561688311688)


def test_avg_high_low_by_regime():
    f = io.StringIO("""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 0.4, Mha,,, 1.0, False, Temperate/Boreal-Humid
      B, 0.5, Mha,,, 1.0, False, Temperate/Boreal-Humid
      C, 0.6, Mha,,, 1.0, False, Tropical-Humid
      """)
    v = vma.VMA(filename=f)
    result = v.avg_high_low()
    assert result[0] == pytest.approx(0.5)
    result = v.avg_high_low(regime='Temperate/Boreal-Humid')
    assert result[0] == pytest.approx(0.45)


def test_avg_high_low_by_region():
    f = io.StringIO("""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 0.4, Mha,,, 1.0, False, Temperate/Boreal-Humid, OECD90
      B, 0.5, Mha,,, 1.0, False, Temperate/Boreal-Humid, OECD90
      C, 0.6, Mha,,, 1.0, False, Tropical-Humid, Latin America
      """)
    v = vma.VMA(filename=f)
    result = v.avg_high_low()
    assert result[0] == pytest.approx(0.5)
    result = v.avg_high_low(region='OECD90')
    assert result[0] == pytest.approx(0.45)


def test_avg_high_low_by_region_with_special_countries():
    f = io.StringIO("""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 0.4, Mha,,, 1.0, False, Temperate/Boreal-Humid, OECD90
      B, 0.5, Mha,,, 1.0, False, Temperate/Boreal-Humid, USA
      C, 0.6, Mha,,, 1.0, False, Tropical-Humid, Latin America
      """)
    v = vma.VMA(filename=f)
    result = v.avg_high_low()
    assert result[0] == pytest.approx(0.5)
    result = v.avg_high_low(region='OECD90')
    assert result[0] == pytest.approx(0.45)
    result = v.avg_high_low(region='USA')
    assert result[0] == pytest.approx(0.5)


def test_no_warnings_in_avg_high_low():
    f = io.StringIO("""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 1.0, Mha,,, 0.0, False
      B, 1.0, Mha,,, 0.0, False
      C, 1.0, Mha,,, 0.0, False
      """)
    with pytest.warns(None) as warnings:
        v = vma.VMA(filename=f)
        _ = v.avg_high_low()
    assert len(warnings) == 0


@pytest.mark.skip(reason="failing on windows; will be rewriting soon")
def test_write_to_file():
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv')
    f.write(r"""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 1.0,,,,
      B, 1.0,,,,
      C, 1.0,,,,
      """)
    f.flush()
    v = vma.VMA(filename=f.name)
    df = v.source_data.copy(deep=True)
    df.loc[0, 'Source ID'] = 'updated source ID'
    v.write_to_file(df)
    with open(f.name) as fid:
        assert 'updated source ID' in fid.read()

@pytest.mark.skip(reason="failing on windows; will be rewriting soon")
def test_reload_from_file():
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv')
    f.write(r"""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      original source ID, 1.0,,,,
      """)
    f.flush()
    v = vma.VMA(filename=f.name)
    df = v.source_data.copy(deep=True)
    assert df.loc[0, 'Source ID'] == 'original source ID'
    f.seek(0)
    f.write(r"""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      updated source ID, 1.0,,,,
      """)
    f.flush()
    v.reload_from_file()
    df = v.source_data.copy(deep=True)
    assert df.loc[0, 'Source ID'] == 'updated source ID'

def test_spelling_correction():
    f = io.StringIO("""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 1.0, Mha,,, 0.0, False,, Asia (sans Japan)
      B, 1.0, Mha,,, 0.0, False,, Middle East & Africa
      """)
    v = vma.VMA(filename=f)
    assert v.df.loc[0, 'Region'] == 'Asia (Sans Japan)'
    assert v.df.loc[1, 'Region'] == 'Middle East and Africa'

def test_categorical_validation():
    f = io.StringIO("""Source ID, Raw Data Input, Original Units, Conversion calculation, Common Units, Weight, Exclude Data?, Thermal-Moisture Regime, World / Drawdown Region
      A, 1.0, Mha,,, 0.0, False, Global Arid, Invalid Region
      B, 1.0, Mha,,, 0.0, False,, USA
      C, 1.0, Mha,,, 0.0, False, Invalid TMR, China
      """)
    v = vma.VMA(filename=f)
    assert pd.isna(v.df.loc[0, 'Region'])
    assert v.df.loc[0, 'TMR'] == 'Global Arid'
    assert v.df.loc[1, 'Region'] == 'USA'
    assert v.df.loc[1, 'TMR'] == ''
    assert v.df.loc[2, 'Region'] == 'China'
    assert v.df.loc[2, 'TMR'] == ''
    assert pd.isna(v.source_data.loc[0, 'World / Drawdown Region'])
    assert pd.isna(v.source_data.loc[2, 'Thermal-Moisture Regime'])

def test_no_filename():
    v = vma.VMA(filename=None)
    assert v.df.empty
    (mean, high, low) = v.avg_high_low()
    assert pd.isna(mean)
    assert pd.isna(high)
    assert pd.isna(low)


def test_invalid_percent_range():
    # Taken from solution/ships/vma_data/Learning_Rate.csv, '10-15%' cannot be converted to float.
    f = io.StringIO("""Source ID,Link,World / Drawdown Region,Specific Geographic Location,Source Validation Code,Year / Date,License Code,Raw Data Input,Original Units,Conversion calculation,Common Units,Weight,Assumptions,Exclude Data?
      A,,World,,,2011,,10-15%,%,,,,,
      B,,World,,,2012,,0.1,%,,,,,
      """)
    v = vma.VMA(filename=f)
    (mean, high, low) = v.avg_high_low()
    assert np.isinf(mean)
    assert pd.isna(high)
    assert not np.isinf(high)
    assert pd.isna(low)
    assert not np.isinf(low)
    # Same CSV, but exclude the invalid entry
    f = io.StringIO("""Source ID,Link,World / Drawdown Region,Specific Geographic Location,Source Validation Code,Year / Date,License Code,Raw Data Input,Original Units,Conversion calculation,Common Units,Weight,Assumptions,Exclude Data?
      A,,World,,,2011,,10-15%,%,,,,,Y
      B,,World,,,2012,,0.1,%,,,,,
      """)
    v = vma.VMA(filename=f)
    (mean, high, low) = v.avg_high_low()
    assert not np.isinf(mean)
    assert not pd.isna(high)
    assert not pd.isna(low)


def test_invalid_float_range():
    f = io.StringIO("""Source ID,Link,World / Drawdown Region,Specific Geographic Location,Source Validation Code,Year / Date,License Code,Raw Data Input,Original Units,Conversion calculation,Common Units,Weight,Assumptions,Exclude Data?
      A,,World,,,2011,,10-15,,,,,,
      B,,World,,,2012,,0.1,,,,,,
      """)
    v = vma.VMA(filename=f)
    (mean, high, low) = v.avg_high_low()
    assert np.isinf(mean)
    assert pd.isna(high)
    assert not np.isinf(high)
    assert pd.isna(low)
    assert not np.isinf(low)
    # Same CSV, but exclude the invalid entry
    f = io.StringIO("""Source ID,Link,World / Drawdown Region,Specific Geographic Location,Source Validation Code,Year / Date,License Code,Raw Data Input,Original Units,Conversion calculation,Common Units,Weight,Assumptions,Exclude Data?
      A,,World,,,2011,,10-15,,,,,,Y
      B,,World,,,2012,,0.1,,,,,,
      """)
    v = vma.VMA(filename=f)
    (mean, high, low) = v.avg_high_low()
    assert not np.isinf(mean)
    assert not pd.isna(high)
    assert not pd.isna(low)


def test_units():
    f = io.StringIO("""Source ID,Link,World / Drawdown Region,Specific Geographic Location,Source Validation Code,Year / Date,License Code,Raw Data Input,Original Units,Conversion calculation,Common Units,Weight,Assumptions,Exclude Data?
        A,,World,,,2011,,0.1,kg,100,g,,,
        B,,World,,,2012,,0.1,kg,100,g,,,
        """)
    v = vma.VMA(filename=f)
    assert v.units == 'g'

    f = io.StringIO("""Source ID,Link,World / Drawdown Region,Specific Geographic Location,Source Validation Code,Year / Date,License Code,Raw Data Input,Original Units,Conversion calculation,Common Units,Weight,Assumptions,Exclude Data?
        A,,World,,,2011,,0.1,kg,,,,,
        B,,World,,,2012,,0.1,kg,100,g,,,
        """)
    v = vma.VMA(filename=f)
    assert v.units == 'g'
    f = io.StringIO("""Source ID,Link,World / Drawdown Region,Specific Geographic Location,Source Validation Code,Year / Date,License Code,Raw Data Input,Original Units,Conversion calculation,Common Units,Weight,Assumptions,Exclude Data?
        A,,World,,,2011,,0.1,kg,,,,,
        B,,World,,,2012,,0.1,kg,,,,,
        """)
    v = vma.VMA(filename=f)
    assert v.units is None