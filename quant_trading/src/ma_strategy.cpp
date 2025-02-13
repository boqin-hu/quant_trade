#include <iostream>
#include <vector>
#include <sqlite3.h>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class MovingAverageStrategy {
private:
    sqlite3* db;
    std::shared_ptr<spdlog::logger> logger;
    int short_window;
    int long_window;

    double calculate_ma(const std::vector<double>& prices, int window) {
        if (prices.size() < window) return 0.0;
        double sum = 0.0;
        for (int i = prices.size() - window; i < prices.size(); ++i) {
            sum += prices[i];
        }
        return sum / window;
    }

    void save_signal(const std::string& stock_code, const std::string& signal_type, 
                    double short_ma, double long_ma) {
        const char* sql = "INSERT INTO strategy_signals (stock_code, signal_type, short_ma, long_ma, timestamp) "
                         "VALUES (?, ?, ?, ?, strftime('%s','now'))";
        sqlite3_stmt* stmt;
        
        if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
            logger->error("准备SQL语句失败: {}", sqlite3_errmsg(db));
            return;
        }

        sqlite3_bind_text(stmt, 1, stock_code.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_text(stmt, 2, signal_type.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_double(stmt, 3, short_ma);
        sqlite3_bind_double(stmt, 4, long_ma);

        if (sqlite3_step(stmt) != SQLITE_DONE) {
            logger->error("插入信号失败: {}", sqlite3_errmsg(db));
        }

        sqlite3_finalize(stmt);
    }

public:
    MovingAverageStrategy(int short_win, int long_win) 
        : short_window(short_win), long_window(long_win), db(nullptr) {
        
        // 初始化日志
        logger = spdlog::basic_logger_mt("strategy_logger", "/Users/huboqin/work/vscode/quant_trading/logs/strategy.log");
        logger->set_level(spdlog::level::info);

        // 连接数据库
        if (sqlite3_open("/Users/huboqin/work/vscode/quant_trading/data/trading.db", &db) != SQLITE_OK) {
            logger->error("无法打开数据库: {}", sqlite3_errmsg(db));
            throw std::runtime_error("数据库连接失败");
        }
    }

    ~MovingAverageStrategy() {
        if (db) {
            sqlite3_close(db);
            logger->info("数据库连接已关闭");
        }
        spdlog::drop_all();
    }

    void analyze(const std::string& stock_code, const std::vector<double>& prices) {
        if (prices.size() < long_window) {
            logger->warn("数据不足，需要至少{}个价格点", long_window);
            return;
        }

        double short_ma = calculate_ma(prices, short_window);
        double long_ma = calculate_ma(prices, long_window);
        std::cout << "short_ma = " << short_ma << " ; " << "long_ma = " << long_ma << std::endl;

        // 检测金叉/死叉
        if (prices.size() >= 2) {
            double prev_short = calculate_ma(std::vector<double>(prices.begin(), prices.end()-1), short_window);
            double prev_long = calculate_ma(std::vector<double>(prices.begin(), prices.end()-1), long_window);

            if (prev_short < prev_long && short_ma > long_ma) {
                logger->info("检测到金叉信号 {}: {:.2f} > {:.2f}", stock_code, short_ma, long_ma);
                save_signal(stock_code, "GOLDEN_CROSS", short_ma, long_ma);
            } else if (prev_short > prev_long && short_ma < long_ma) {
                logger->info("检测到死叉信号 {}: {:.2f} < {:.2f}", stock_code, short_ma, long_ma);
                save_signal(stock_code, "DEATH_CROSS", short_ma, long_ma);
            } else if (prev_short > prev_long && short_ma > long_ma) {
                logger->info("检测到量价齐升 {}: {:.2f} < {:.2f}", stock_code, short_ma, long_ma);
                save_signal(stock_code, "GOLDEN_CROSS", short_ma, long_ma);
            }
            std::cout << "prev_short = " << prev_short << " ; " << "prev_long = " << prev_long << std::endl;

        }
    }
};

int main() {
    try {
        MovingAverageStrategy strategy(10, 50);
        
        // 测试数据：假设获取到50个价格点
        std::vector<double> test_prices;
        test_prices.reserve(200);
        for (int i = 0; i < 50; ++i) {
            strategy.analyze("SH600519", test_prices);
            test_prices.emplace_back(100.0 + i * 0.5);
        }
        for (int i = 0; i < 50; ++i) {
            strategy.analyze("SH600519", test_prices);
            test_prices.emplace_back(test_prices[49] - i * 0.5);
        }
        for (int i = 0; i < 50; ++i) {
            strategy.analyze("SH600519", test_prices);
            test_prices.emplace_back(test_prices[99] + i * 1.5);
        }
        
        // strategy.analyze("SH600519", test_prices);
    } catch (const std::exception& e) {
        std::cerr << "策略初始化失败: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
