cmake_minimum_required(VERSION 3.20)
project(QuantTrading)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Homebrew安装路径
set(HOMEBREW_PREFIX "/opt/homebrew")

# 包含目录
include_directories(
    ${HOMEBREW_PREFIX}/include
    ${HOMEBREW_PREFIX}/include/spdlog
    ${HOMEBREW_PREFIX}/include/nlohmann
)

# 显式设置SQLite路径
set(SQLITE3_INCLUDE_DIRS "/opt/homebrew/opt/sqlite/include")
set(SQLITE3_LIBRARIES "/opt/homebrew/opt/sqlite/lib/libsqlite3.dylib")

# 显式设置spdlog和fmt路径
set(SPDLOG_INCLUDE_DIR "${HOMEBREW_PREFIX}/include")
set(SPDLOG_LIB "${HOMEBREW_PREFIX}/lib/libspdlog.dylib")
set(FMT_INCLUDE_DIR "${HOMEBREW_PREFIX}/include")
set(FMT_LIB "${HOMEBREW_PREFIX}/lib/libfmt.dylib")

# 添加可执行文件
add_executable(ma_strategy 
    src/ma_strategy.cpp
)

# 链接库
target_link_libraries(ma_strategy
    PRIVATE 
    ${SQLITE3_LIBRARIES}
    ${SPDLOG_LIB}
    ${FMT_LIB}
    pthread
)

# 设置编译器标志
target_compile_options(ma_strategy PRIVATE
    -L${HOMEBREW_PREFIX}/lib
    -I${HOMEBREW_PREFIX}/include
)
