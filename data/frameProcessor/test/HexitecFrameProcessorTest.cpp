#define BOOST_TEST_MODULE "HexitecFrameProcessorTests"
#define BOOST_TEST_MAIN
#include <boost/test/unit_test.hpp>
#include <boost/shared_ptr.hpp>

#include <iostream>

#include "HexitecReorderPlugin.h"

class HexitecReorderPluginTestFixture
{
public:
	HexitecReorderPluginTestFixture()
	{
		std::cout << "HexitecReorderPluginTestFixture constructor" << std::endl;
	}

	~HexitecReorderPluginTestFixture()
	{
		std::cout << "HexitecReorderPluginTestFixture destructor" << std::endl;
	}
};

BOOST_FIXTURE_TEST_SUITE(HexitecReorderPluginUnitTest, HexitecReorderPluginTestFixture);

BOOST_AUTO_TEST_CASE(HexitecReorderPluginTestFixture)
{
	std::cout << "HexitecReorderPluginTestFixture test case" << std::endl;
}

BOOST_AUTO_TEST_SUITE_END();
