from nose.tools import *
import random
import sys

#from excalibur.fem import ExcaliburFemConfig, ExcaliburFem, ExcaliburFemError
from excalibur.fem import ExcaliburFem, ExcaliburFemError
from excalibur.parameter import *

class TestExcaliburFemError:

    def test_error_value(self):

        value = 'Test error value'
        with assert_raises_regexp(ExcaliburFemError, value):
            raise ExcaliburFemError(value)


class TestExcaliburMissingApiLibrary:

    @classmethod
    def setup_class(cls):

        cls.fem_id = 1234
        cls.fem_address = '192.168.0.100'
        cls.fem_port = 6969
        cls.data_address = '10.0.2.1'
        cls.restore_fem_api_stem = ExcaliburFem.api_stem
        ExcaliburFem.api_stem = 'fem_api_missing'
        ExcaliburFem.use_stub_api = False
        ExcaliburFem._fem_api = None

    @classmethod
    def teardown_class(cls):

        ExcaliburFem.fem_api_stem = cls.restore_fem_api_stem
        ExcaliburFem._fem_api = None

    def test_missing_library(self):

        with assert_raises_regexp(ExcaliburFemError, 'Failed to load API module: No module named'):
            fem = ExcaliburFem(self.fem_id, self.fem_address, self.fem_port, self.data_address)


class TestExcaliburFem:

    @classmethod
    def setup_class(cls):
        cls.fem_id = 1234
        cls.fem_address = '192.168.0.100'
        cls.fem_port = 6969
        cls.data_address = '10.0.2.1'

        # Enable use of stub API for testing
        ExcaliburFem.use_stub_api = True

        # Unload any previously loaded API module, to ensure we use the correct stub version for this test class
        if ExcaliburFem._fem_api is not None:
            del sys.modules[ExcaliburFem._fem_api.__name__]
            ExcaliburFem._fem_api = None
            
        cls.the_fem = ExcaliburFem(
            cls.fem_id, cls.fem_address, cls.fem_port, cls.data_address
        )

    def test_legal_fem_id(self):

        assert_equal(self.fem_id, self.the_fem.get_id())

    def test_illegal_fem_id(self):

        id = -1
        with assert_raises(ExcaliburFemError) as cm:
            bad_fem = ExcaliburFem(id, self.fem_address, self.fem_port, self.data_address)
        assert_equal(cm.exception.value, 'Failed to initialise FEM connection: Illegal ID specified')

    def test_fem_id_exception(self):

        temp_fem = ExcaliburFem(1, self.fem_address, self.fem_port, self.data_address)
        temp_fem.fem_handle = None
        with assert_raises_regexp(
                ExcaliburFemError, 'get_id: resolved FEM object pointer to null'):
            temp_fem.get_id()

    def test_double_close(self):

        the_fem = ExcaliburFem(0, self.fem_address, self.fem_port, self.data_address)
        the_fem.close()
        with assert_raises(ExcaliburFemError) as cm:
            the_fem.close()
        assert_equal(cm.exception.value, 'close: FEM object pointer has null FEM handle')

    def test_legal_get_ints(self):

        chip_id = 0
        param_id = 1001
        param_len = 10
        (rc, values) = self.the_fem.get_int(chip_id, param_id, param_len)

        assert_equal(rc, FEM_RTN_OK)
        assert_equal(len(values), param_len)
        assert_equal(values, list(range(param_id, param_id+param_len)))

    def test_get_int_exception(self):

        chip_id = 0
        param_id = 1001
        param_len = 10

        temp_fem = ExcaliburFem(1, self.fem_address, self.fem_port, self.data_address)
        temp_fem.fem_handle = None

        with assert_raises_regexp(
                ExcaliburFemError, 'get_int: resolved FEM object pointer to null'):
            temp_fem.get_int(chip_id, param_id, param_len)

    def test_legal_set_single_int(self):

        chip_id = 0
        param_id = 1001
        value = 1234

        rc = self.the_fem.set_int(chip_id, param_id, value)

        assert_equal(rc, FEM_RTN_OK)

    def test_legal_set_ints(self):

        chip_id = 0
        param_id = 1001
        param_len = 10
        values = list(range(param_id, param_id + param_len))

        rc = self.the_fem.set_int(chip_id, param_id, values)

        assert_equal(rc, FEM_RTN_OK)

    def test_illegal_set_int(self):

        chip_id = 0
        param_id = 10001
        values = [3.14]*10

        with assert_raises(ExcaliburFemError) as cm:
            rc = self.the_fem.set_int(chip_id, param_id, values)
        assert_equal(cm.exception.value, 'set_int: non-integer value specified')

    def test_legal_set_and_get_int(self):

        chip_id = 0
        param_id = 10002
        param_len = 100
        values_in = [random.randint(0, 1000000) for x in range(param_len)]

        rc = self.the_fem.set_int(chip_id, param_id, values_in)
        assert_equal(rc, FEM_RTN_OK)

        (rc, values_out) = self.the_fem.get_int(chip_id, param_id, param_len)
        assert_equal(rc, FEM_RTN_OK)
        assert_equal(values_in, values_out)
        
    def test_legal_set_string(self):
        
        chip_id = 0
        param_id = 1000
        values = [u"these", u"are", u"strings"]
        
        rc = self.the_fem.set_string(chip_id, param_id, values)
        assert_equal(rc, FEM_RTN_OK)
        
    def test_legal_cmd(self):

        chip_id = 0
        cmd_id = 1
        rc = self.the_fem.cmd(chip_id, cmd_id)
        assert_equal(rc, FEM_RTN_OK)

    def test_illegal_cmd(self):

        chip_id  = 0;
        cmd_id = -1
        rc = self.the_fem.cmd(chip_id, cmd_id)
        assert_equal(rc, FEM_RTN_UNKNOWNOPID)

    def test_cmd_exception(self):

        chip_id = 0
        cmd_id = 1

        temp_fem = ExcaliburFem(1, self.fem_address, self.fem_port, self.data_address)
        temp_fem.fem_handle = None

        with assert_raises_regexp(
                ExcaliburFemError, 'cmd: resolved FEM object pointer to null'):
            temp_fem.cmd(chip_id, cmd_id)
