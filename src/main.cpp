#include <iostream>
#include <nlohmann/json.hpp>
#include <curl/curl.h>
#include <vector>
#include <chrono>
#include <thread>
#include <cmath>

using json = nlohmann::json;

// 东方财富API配置
const std::string API_BASE_URL = "https://api.eastmoney.com";
const std::string ACCOUNT_ID = "YOUR_ACCOUNT_ID";
const std::string ACCESS_TOKEN = "YOUR_ACCESS_TOKEN";

// cURL写回调函数
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* output) {
    size_t total_size = size * nmemb;
    output->append((char*)contents, total_size);
    return total_size;
}

// 移动平均计算器
class MovingAverageCalculator {
private:
    int period;
    std::vector<double> prices;
    
public:
    MovingAverageCalculator(int p) : period(p) {}
    
    void addPrice(double price) {
        prices.push_back(price);
        if(prices.size() > period) {
            prices.erase(prices.begin());
        }
    }
    
    double calculate() const {
        if(prices.size() < period) return NAN;
        double sum = 0.0;
        for(double p : prices) sum += p;
        return sum / period;
    }
};

// 交易信号生成器
class TradeSignalGenerator {
private:
    MovingAverageCalculator ma10;
    MovingAverageCalculator ma50;
    double lastMa10 = 0;
    double lastMa50 = 0;
    
public:
    TradeSignalGenerator() : ma10(10), ma50(50) {}
    
    // 更新行情数据并生成信号
    std::string generateSignal(double price) {
        ma10.addPrice(price);
        ma50.addPrice(price);
        
        double currentMa10 = ma10.calculate();
        double currentMa50 = ma50.calculate();
        
        if(std::isnan(currentMa10) || std::isnan(currentMa50)) {
            return "HOLD";
        }
        
        std::string signal = "HOLD";
        
        if(lastMa10 < lastMa50 && currentMa10 > currentMa50) {
            signal = "BUY";
        }
        else if(lastMa10 > lastMa50 && currentMa10 < currentMa50) {
            signal = "SELL";
        }
        
        lastMa10 = currentMa10;
        lastMa50 = currentMa50;
        
        return signal;
    }
};

// 订单执行管理器
class OrderExecutionManager {
private:
    CURL* curl;
    
public:
    OrderExecutionManager() {
        curl = curl_easy_init();
    }
    
    ~OrderExecutionManager() {
        if(curl) curl_easy_cleanup(curl);
    }
    
    // 执行交易订单
    bool executeOrder(const std::string& symbol, const std::string& action, int quantity) {
        if(!curl) return false;
        
        std::string url = API_BASE_URL + "/trade/order?account=" + ACCOUNT_ID;
        std::string postData = json({
            {"symbol", symbol},
            {"action", action},
            {"quantity", quantity},
            {"token", ACCESS_TOKEN}
        }).dump();
        
        std::string response;
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        
        CURLcode res = curl_easy_perform(curl);
        if(res != CURLE_OK) {
            std::cerr << "API请求失败: " << curl_easy_strerror(res) << std::endl;
            return false;
        }
        
        try {
            auto result = json::parse(response);
            return result["success"].get<bool>();
        } catch(...) {
            return false;
        }
    }
};

// East Money API wrapper
class EastMoneyAPI {
public:
    EastMoneyAPI(const std::string& api_key) : api_key_(api_key) {}
    
    std::vector<double> getHistoricalPrices(const std::string& symbol, int minutes) {
        std::vector<double> prices;
        CURL* curl = curl_easy_init();
        if(curl) {
            std::string url = "https://api.eastmoney.com/market/history?symbol=" 
                            + symbol + "&minutes=" + std::to_string(minutes);
            std::string response;
            
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, createAuthHeader());
            
            CURLcode res = curl_easy_perform(curl);
            if(res == CURLE_OK) {
                prices = parsePriceData(response);
            }
            curl_easy_cleanup(curl);
        }
        return prices;
    }
    
    bool placeOrder(const std::string& symbol, int quantity, bool is_buy) {
        CURL* curl = curl_easy_init();
        if(curl) {
            std::string url = "https://trade.eastmoney.com/api/order";
            std::string postData = "symbol=" + symbol 
                                 + "&quantity=" + std::to_string(quantity)
                                 + "&type=" + (is_buy ? "buy" : "sell");
            
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, createAuthHeader());
            
            CURLcode res = curl_easy_perform(curl);
            curl_easy_cleanup(curl);
            return (res == CURLE_OK);
        }
        return false;
    }

private:
    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* s) {
        size_t newLength = size * nmemb;
        s->append((char*)contents, newLength);
        return newLength;
    }
    
    struct curl_slist* createAuthHeader() {
        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, ("Authorization: Bearer " + api_key_).c_str());
        return headers;
    }
    
    std::vector<double> parsePriceData(const std::string& json) {
        std::vector<double> prices;
        try {
            auto j = nlohmann::json::parse(json);
            for (auto& item : j["data"]["klines"]) {
                prices.push_back(item["close"].get<double>());
            }
        } catch (const std::exception& e) {
            std::cerr << "JSON解析错误: " << e.what() << std::endl;
        }
        return prices;
    }

private:
    std::string api_key_;
};

// Moving Average Calculator
class MovingAverage {
public:
    MovingAverage(int period) : period_(period) {}
    
    void addPrice(double price) {
        prices_.push_back(price);
        if (prices_.size() > period_) {
            prices_.erase(prices_.begin());
        }
    }
    
    double calculate() const {
        if (prices_.empty()) return 0.0;
        double sum = 0.0;
        for (double price : prices_) {
            sum += price;
        }
        return sum / prices_.size();
    }

private:
    int period_;
    std::vector<double> prices_;
};

// Trading Strategy
class MACrossoverStrategy {
public:
    MACrossoverStrategy(EastMoneyAPI& api)
        : api_(api), short_ma_(10), long_ma_(50), position_(0) {}
        
    void run(const std::string& symbol) {
        while (true) {
            auto prices = api_.getHistoricalPrices(symbol, 50);
            if (!prices.empty()) {
                for (double price : prices) {
                    short_ma_.addPrice(price);
                    long_ma_.addPrice(price);
                }
                
                double short_ma = short_ma_.calculate();
                double long_ma = long_ma_.calculate();
                
                if (position_ <= 0 && short_ma > long_ma) {
                    // Buy signal
                    if (api_.placeOrder(symbol, 100, true)) {
                        position_ = 100;
                        std::cout << "Bought 100 shares at " << prices.back() << std::endl;
                    }
                } else if (position_ > 0 && short_ma < long_ma) {
                    // Sell signal
                    if (api_.placeOrder(symbol, 100, false)) {
                        position_ = 0;
                        std::cout << "Sold 100 shares at " << prices.back() << std::endl;
                    }
                }
            }
            
            std::this_thread::sleep_for(std::chrono::minutes(1));
        }
    }

private:
    EastMoneyAPI& api_;
    MovingAverage short_ma_;
    MovingAverage long_ma_;
    int position_;
};

int main() {
    // TODO: Get API key from config
    EastMoneyAPI api("your_api_key_here");
    MACrossoverStrategy strategy(api);
    
    std::string symbol = "SH600519"; // Example: Kweichow Moutai
    strategy.run(symbol);
    
    return 0;
}
