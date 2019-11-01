"""
Test Cases for the Hexitec Fem in hexitec
Christian Angelsen, STFC Detector Systems Software Group
"""

"""
Test Cases for the QEMII Fem in qemii.detector
Adam Neaves, STFC Detector Systems Software Group
"""

import sys
import pytest
import time

from hexitec.HexitecFem import HexitecFem, HexitecFemError

from odin.adapters.parameter_tree import ParameterTreeError

from socket import error as socket_error

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, call, patch, ANY
else:                         # pragma: no cover
    from mock import Mock, MagicMock, call, patch, ANY


class FemTestFixture(object):

    def __init__(self):

        self.ip = "127.0.0.1"
        self.port = 8888
        self.id = 0
        self.frame_size = 7344

        # FPGA base addresses
        self.rdma_addr = {
            "sequencer":       0xB0000000,
            "receiver":        0xC0000000,
            "frm_gate":        0xD0000000
        }

        self.vector_file_dir = "fake/vector/file/dir"
        self.vector_file = "FakeVectorFile.txt"
        self.vector_length = 3
        self.vector_loop = 1

        with patch("hexitec.HexitecFem.RdmaUDP"):
            self.fem = HexitecFem(self.ip, self.port, self.id,
                                self.ip, self.ip, self.ip, self.ip)

            self.fem.connect()

@pytest.fixture()
def test_fem():
    """Test Fixture for testing the Fem"""

    test_fem = FemTestFixture()
    yield test_fem


class TestFem():

    def test_init(self, test_fem):
        """Assert the initilisation of the Fem class works"""
        assert test_fem.fem.ip_address == test_fem.ip
        # assert test_fem.fem.vector_file_dir == test_fem.vector_file_dir
        assert test_fem.fem.id == test_fem.id

    def test_nonzero_id(self, test_fem):
        """Assert the vector file is ignored if ID is not 0"""
        fem = HexitecFem(test_fem.ip, test_fem.port, 1,
                     test_fem.ip, test_fem.ip, test_fem.ip, test_fem.ip)
        assert fem.id == 1

    def test_connect(self, test_fem):
        """Assert the connect method creates the rdma as expected"""
        with patch("hexitec.HexitecFem.RdmaUDP") as mock_rdma:
            test_fem.fem.connect()

            mock_rdma.assert_called_with(test_fem.ip, 61650,
                                         test_fem.ip, 61651,
                                         test_fem.ip, 61650,
                                         test_fem.ip, 61651,
                                         2000000, 9000, 20)
            assert test_fem.fem.x10g_rdma.ack is True

    def test_connect_fails(self, test_fem):
        """Assert the connect method Exception handling works"""

        with patch('hexitec.HexitecFem.RdmaUDP') as rdma_mock:
            
            rdma_mock.side_effect = socket_error()
            with pytest.raises(socket_error) as exc_info:
                test_fem.fem.connect()
            assert exc_info.type is socket_error
            assert exc_info.value.args[0] == "Failed to setup Control connection: "

    def test_set_image_size(self, test_fem):

        address_pixel_count = test_fem.rdma_addr['receiver'] | 0x01
        address_pixel_size = test_fem.rdma_addr['receiver'] + 4

        # test_fem.fem.set_image_size(102, 288, 11, 16)
        test_fem.fem.set_image_size(160, 160, 14, 16)

        assert test_fem.fem.image_size_x == 160 #102
        assert test_fem.fem.image_size_y == 160 #288
        assert test_fem.fem.image_size_p == 14  #11
        assert test_fem.fem.image_size_f == 16

        pixel_count_max = (160*160)//2
        data = (pixel_count_max & 0x1FFFF) -1
        test_fem.fem.x10g_rdma.write.assert_has_calls(
            [call(address_pixel_count, data, ANY),
                call(address_pixel_size, 0x3, ANY)]
        )

        # Repeat for 80x80, single sensor?
        # test_fem.fem.set_image_size(102, 288, 11, 16)
        test_fem.fem.set_image_size(80, 80, 14, 16)

        assert test_fem.fem.image_size_x == 80
        assert test_fem.fem.image_size_y == 80
        assert test_fem.fem.image_size_p == 14
        assert test_fem.fem.image_size_f == 16

        pixel_count_max = (80*80)//2
        data = (pixel_count_max & 0x1FFFF) -1
        test_fem.fem.x10g_rdma.write.assert_has_calls(
            [call(address_pixel_count, data, ANY),
                call(address_pixel_size, 0x3, ANY)]
        )



    def test_set_image_size_wrong_pixel(self, test_fem):

        test_fem.fem.set_image_size(102, 288, 0, 16)

        assert test_fem.fem.image_size_x == 102
        assert test_fem.fem.image_size_y == 288
        assert test_fem.fem.image_size_p == 0
        assert test_fem.fem.image_size_f == 16

        assert not test_fem.fem.x10g_rdma.write.called

    def test_data_stream(self, test_fem):
        ''' Also covers frame_gate_settings(), frame_gate_trigger() '''
        frame_num = 10
        frame_gap = 0
        # data_stream subtracts 1 from frame_num before
        #   passing it onto frame_gate_settings
        test_fem.fem.data_stream(frame_num+1)

        test_fem.fem.x10g_rdma.write.assert_has_calls([
            call(test_fem.rdma_addr["frm_gate"] + 1, frame_num, ANY),
            call(test_fem.rdma_addr["frm_gate"] + 2, frame_gap, ANY),
            call(test_fem.rdma_addr["frm_gate"], 0, ANY),
            call(test_fem.rdma_addr["frm_gate"], 1, ANY),
            call(test_fem.rdma_addr["frm_gate"], 0, ANY)
        ])

    # frame_gate_trigger called by data_stream()
    # def test_frame_gate_trigger(self, test_fem):

    #     test_fem.fem.frame_gate_trigger()

    #     test_fem.fem.x10g_rdma.write.assert_has_calls([
    #         call(test_fem.rdma_addr["frm_gate"], 0, ANY),
    #         call(test_fem.rdma_addr["frm_gate"], 1, ANY),
    #         call(test_fem.rdma_addr["frm_gate"], 0, ANY)
    #     ])

    def test_cleanup(self, test_fem):
        test_fem.fem.cleanup()

        test_fem.fem.x10g_rdma.close.assert_called_with()

    def test_disconnect_hardware(self, test_fem):
        test_fem.fem.hardware_connected = True
        test_fem.fem.disconnect_hardware("test")
        # time.sleep(0.5)

        assert test_fem.fem.hardware_connected == False

    def test_connect_hardware_fails(self, test_fem):

        with patch('hexitec.HexitecFem.RdmaUDP') as rdma_mock:
            
            # Fein error connecting to camera
            rdma_mock.side_effect = HexitecFemError()
            test_fem.fem.connect_hardware()
            time.sleep(0.1)
            assert test_fem.fem._get_status_error() == "Failed to connect with camera: "
            assert test_fem.fem._get_status_message() == "Is camera powered?"

            # Fein unexpected Exception connecting to camera
            test_fem.fem.hardware_connected = False
            rdma_mock.side_effect = Exception()
            test_fem.fem.connect_hardware()
            time.sleep(0.1)
            assert test_fem.fem._get_status_error() == "Uncaught Exception; Failed to establish camera connection: "

        # Don't Mock, error because we couldn't setup a connection        
        test_fem.fem.connect_hardware("test")

        time.sleep(0.1)
        # assert test_fem.fem._get_status_error() == "Failed to setup Control connection:"

        # Provoke error by pretending connection already exists
        test_fem.fem.hardware_connected = True

        test_fem.fem.connect_hardware("test")
        time.sleep(0.1)
        assert test_fem.fem._get_status_error() == "Connection already established"

    def test_disconnect_hardware_fails(self, test_fem):
        test_fem.fem.hardware_connected = False

        test_fem.fem.disconnect_hardware("test")
        time.sleep(0.1)
        assert test_fem.fem._get_status_error() == "Failed to disconnect: No connection to disconnect"

    def test_initialise_hardware(self, test_fem):
        test_fem.fem.initialise_hardware("test")

        # time.sleep(0.1)
        # assert test_fem.fem.hardware_connected == True
        # assert test_fem.fem._get_status_message() == "Acquiring data.."
        assert test_fem.fem.operation_percentage_complete == 0

    #TODO: status_error == "", unless initialise_system littered with print's..
    # def test_initialise_hardware_fails_HexitecFemError(self, test_fem):

    #     # This block takes frekkin' aaages, And:

    #     test_fem.fem.hardware_connected = True
    #     # test_fem.fem.connect_hardware("test")
    #     # Fein error initialising camera
    #     test_fem.fem.x10g_rdma.write = Mock()
    #     test_fem.fem.x10g_rdma.write.side_effect = HexitecFemError()
    #     test_fem.fem.initialise_hardware()
    #     time.sleep(0.2)     # Sleep required or assert finds "" == "Failed..."
    #     assert test_fem.fem._get_status_error() == "Failed to initialise camera: "

    #     test_fem.fem.hardware_connected = False
    #     test_fem.fem.initialise_hardware("test")

    #     time.sleep(0.1)
    #     assert test_fem.fem._get_status_error() == "Failed to initialise camera: No connection established"

    #     test_fem.fem.hardware_connected = True
    #     test_fem.fem.hardware_initialising = True
    #     test_fem.fem.initialise_hardware("test")

    #     time.sleep(0.1)
    #     assert test_fem.fem._get_status_error() == "Failed to initialise camera: Hardware sensors busy initialising"
    #     test_fem.fem._set_status_error("")

    # #TODO: status_error == "", unless initialise_system littered with print's..
    # def test_initialise_hardware_fails_Exception(self, test_fem):

    #     test_fem.fem.hardware_connected = True
    #     # Fein unexpected Exception initialising camera
    #     test_fem.fem.x10g_rdma.write = Mock()
    #     test_fem.fem.x10g_rdma.write.side_effect = Exception()
    #     test_fem.fem.initialise_hardware()
    #     time.sleep(0.1)
    #     assert test_fem.fem._get_status_error() == "Uncaught Exception; Camera initialisation failed: "

    def test_collect_data(self, test_fem):
        test_fem.fem.collect_data("test")

        # time.sleep(0.1)
        # assert test_fem.fem.hardware_connected == True
        # assert test_fem.fem._get_status_message() == "Acquiring data.."
        assert test_fem.fem.operation_percentage_complete == 0

    def test_collect_data_fails(self, test_fem):
        test_fem.fem.hardware_connected = False
        test_fem.fem.collect_data("test")

        time.sleep(0.1)
        assert test_fem.fem._get_status_error() == "Failed to collect data: No connection established"

        test_fem.fem.hardware_connected = True
        test_fem.fem.hardware_initialising = True
        test_fem.fem.collect_data("test")

        time.sleep(0.1)
        assert test_fem.fem._get_status_error() == "Failed to collect data: Hardware sensors busy initialising"

    def test_accessor_functions(self, test_fem):

        number_frames = 1001
        test_fem.fem._set_number_frames(number_frames)
        assert test_fem.fem._get_number_frames() == number_frames

        for bEnabled in True, False:
            test_fem.fem._set_dark_correction(bEnabled)
            assert test_fem.fem._get_dark_correction() == bEnabled

            test_fem.fem._set_test_mode_image(bEnabled)
            assert test_fem.fem._get_test_mode_image() == bEnabled

            test_fem.fem.set_debug(bEnabled)
            assert test_fem.fem.get_debug() == bEnabled

    def test_read_response(self, test_fem):

        test_fem.fem.set_debug(True)

        return_values = [0, 714158145, 0, 808520973, 0, 13]
        test_fem.fem.x10g_rdma.read = Mock() #Mock(return_value=0)
        test_fem.fem.x10g_rdma.read.side_effect = return_values

        address = 0xE0000011 #0xE0000200
        status = test_fem.fem.read_response()

        test_fem.fem.x10g_rdma.read.assert_called_with(address, ANY)
        assert status == '\x910A01\r\r'

    def test_read_response_failed(self, test_fem):

        test_fem.fem.x10g_rdma.read = Mock(return_value=1)

        address = 0xE0000011 #0xE0000200

        with pytest.raises(HexitecFemError) as exc_info:
            test_fem.fem.read_response()
        assert exc_info.type is HexitecFemError
        assert exc_info.value.args[0] == "read_response aborted"

        # def test_read_response_failed(self, test_fem):

        # test_fem.fem.x10g_rdma.read = Mock(return_value=1)

        # address = 0xE0000011 #0xE0000200

        # with pytest.raises(HexitecFemError) as exc_info:
        #     test_fem.fem.read_response()
        # assert exc_info.type is HexitecFemError
        # assert exc_info.value.args[0] == "read_response aborted"

    def test_connect_hardware(self, test_fem):
        with patch("hexitec.HexitecFem.RdmaUDP") as mock_rdma:

            test_fem.fem.connect_hardware("test")

            time.sleep(0.1)
            assert test_fem.fem.hardware_connected == True




