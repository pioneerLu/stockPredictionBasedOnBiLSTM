# 仅仅添加止盈止损，能赚1K
# 创建策略
class TestStrategy(bt.Strategy):
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.datalow = self.datas[0].low
        self.datahigh = self.datas[0].high
        self.dataopen = self.datas[0].open
        self.position_threshold = 10 # 仓位阈值
        self.now_date = None # 当前日期
        self.portfolio = portfolio # 资产值
        
    def next(self):
        # 获得当前日期
        dt = self.datas[0].datetime.date(0)

        ndt = dt.strftime('%Y-%m-%d')
        

        # 获取当日日线预测收盘价
        predicted_price = df1[df1['Date'] == ndt]['Predicted_Price'].values[0]
        # 如果这是前两次数据，不执行任何操作
        if len(self.dataclose) < 3:
            return
        # 如果日期改变，记录总资产
        if dt != self.now_date:
            self.now_date = dt
            # 将投资组合价值存储到 portfolio 中
            value = self.broker.getvalue()
            self.portfolio = self.portfolio._append({'datetime': dt, 'value': value}, ignore_index=True)
            

        # 计算近三次的开盘增长率
        close_growth_rate = (self.dataclose[0] - self.dataclose[-3]) / self.dataclose[-3]
        open_growth_rate = (self.dataopen[0] - self.dataopen[-3]) / self.dataopen[-3]
        #
        # 如果有未完成的订单，不执行任何操作
        if self.order:
            return
        # 交易的是指数，position不能小于0
        # 如果当前持仓小于持仓阈值，且开盘增长率大于0.1
        if self.position.size < self.position_threshold and self.position.size > 0:
            # 如果当前收盘价小于预测收盘价，且开盘增长率大于-0.2%,则买入
            if self.dataclose[0] < predicted_price and open_growth_rate > -0.002:
                self.order = self.buy()
            # 如果当前收盘价大于预测收盘价，且开盘增长率小于-0.1%,则卖出
            elif self.dataclose[0] > predicted_price and open_growth_rate < -0.001:
                self.order = self.sell()
        # 如果没有持仓
        elif self.position.size == 0:
            # 如果当前收盘价小于预测收盘价，且开盘增长率大于-0.2%,则买入
            if self.dataclose[0] < predicted_price and open_growth_rate > -0.002:
                self.order = self.buy()
                
    def notify_order(self, order):
        # self.trade_analyzer.notify_order(order)
        if order.status in [order.Submitted, order.Accepted]:
            return

        if self.order:
            self.order = None

        # 买与卖的止盈止损订单
        if order.issell() and not self.position: # 卖出时立刻着手买入
            self.buy(exectype=bt.Order.Limit, price=order.executed.price * 0.95)  # 止盈，97块及以下都买！98就不买了
        elif order.isbuy() and self.position.size < self.position_threshold: # 买入时立刻着手卖出
            self.sell(exectype=bt.Order.Stop, price=order.executed.price * 0.95)    # 止损，掉太多了就赶紧卖出去！
            self.sell(exectype=bt.Order.Limit, price=order.executed.price * 1.05)  # 止盈，涨到103就卖！102赚太少不卖了。