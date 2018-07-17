#define BOOST_TEST_MODULE "HexitecFrameProcessorTests"
#define BOOST_TEST_MAIN
#include <boost/test/unit_test.hpp>
#include <boost/shared_ptr.hpp>

#include <iostream>

#include "HexitecProcessPlugin.h"

class HexitecProcessPluginTestFixture
{
public:
	HexitecProcessPluginTestFixture()
	{
		std::cout << "HexitecProcessPluginTestFixture constructor" << std::endl;
	}

	~HexitecProcessPluginTestFixture()
	{
		std::cout << "HexitecProcessPluginTestFixture destructor" << std::endl;
	}
};

BOOST_FIXTURE_TEST_SUITE(HexitecProcessPluginUnitTest, HexitecProcessPluginTestFixture);

BOOST_AUTO_TEST_CASE(HexitecProcessPluginTestFixture)
{
	std::cout << "HexitecProcessPluginTestFixture test case" << std::endl;
}

BOOST_AUTO_TEST_SUITE_END();
