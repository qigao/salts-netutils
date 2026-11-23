if(NOT DEFINED ENV{RE2C_ROOT} OR NOT IS_DIRECTORY "$ENV{RE2C_ROOT}")
    message(FATAL_ERROR
        "RE2C_ROOT must name the host tools directory from Qigao.Re2c.Binary. "
        "Set RE2C_ROOT to the restored host SDK before configuring.")
endif()
unset(RE2C_EXECUTABLE CACHE)
unset(RE2C_EXECUTABLE)
find_program(RE2C_EXECUTABLE re2c
             PATHS "$ENV{RE2C_ROOT}/bin"
             NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH REQUIRED)

# Lemon and its paired template run on the build host, including cross builds.
if("$ENV{LEMON_ROOT}" STREQUAL "")
    message(FATAL_ERROR "LEMON_ROOT must name the restored Qigao.Lemon.Binary host payload")
endif()
unset(LEMON_EXECUTABLE CACHE)
unset(LEMON_EXECUTABLE)
unset(LEMPAR CACHE)
unset(LEMPAR)
find_program(LEMON_EXECUTABLE lemon
             PATHS "$ENV{LEMON_ROOT}/bin"
             NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH REQUIRED)
find_file(LEMPAR lempar.c
          PATHS "$ENV{LEMON_ROOT}/share/lemon"
          NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH REQUIRED)
