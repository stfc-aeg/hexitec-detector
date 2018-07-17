ifndef SRC_DIR
	SRC_DIR = src
endif

ifndef INC_DIR
	INC_DIR = include
endif

ifndef OBJ_DIR
	OBJ_DIR = .
endif

ifndef LIB_DIR
	LIB_DIR = .
endif

CXXFLAGS = -fPIC -Wall -I${INC_DIR}
#LDFLAGS = -shared 
LDFLAGS = 


ifdef BOOST_ROOT
	CXXFLAGS += -I${BOOST_ROOT}/include
	LDFLAGS += -L${BOOST_ROOT}/lib 
endif

LDFLAGS += -lboost_system -lboost_thread

SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
OBJECTS= $(SOURCES:$(SRC_DIR)/%.cpp=$(OBJ_DIR)/%.o)
TARGET = $(LIB_DIR)/libfem_api.a

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(AR) $(ARFLAGS) $@ $(OBJECTS)      
        
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) $< -c -o $@
        
clean:
	rm -f $(TARGET)
	rm -f $(OBJECTS)
	
../../excalibur/fem_api_parameters.py: ${INC_DIR}/femApi.h
	@/bin/echo "Generating $@ ..."
	@python generate_fem_api_parameters.py $< $@