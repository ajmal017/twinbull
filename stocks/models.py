import logging
from datetime import date, datetime

from django.db import models

from utils.nse_bhav import Nse

logger = logging.getLogger(__name__)


class Stock(models.Model):
    NIFTY_50 = 0
    NIFTY_NEXT_50 = 1
    NIFTY_MIDCAP = 2
    NIFTY_CHOICES = ((NIFTY_50, 'Nifty 50'),
                     (NIFTY_NEXT_50, 'Nifty Next 50'),
                     (NIFTY_MIDCAP, 'Nifty Midcap'))

    symbol = models.CharField(max_length=100, verbose_name="Symbol", db_index=True)
    isin = models.CharField(max_length=30, verbose_name="ISIN")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Stock created at")
    moneycontrol_link = models.TextField(verbose_name='MoneyControl.com', null=True, default=None, blank=True)
    moneycontrol_stock_id = models.CharField(verbose_name='Moneycontrol stock id', null=True, blank=True, default=None,
                                             max_length=100)
    broad_market_indices = models.PositiveSmallIntegerField(choices=NIFTY_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.symbol


class StockHistoryManager(models.Manager):
    def update_stocks(self, by_trade_date=date.today()):
        symbols_instance = Stock.objects.all().values('id', 'symbol')
        symbols = {stock['symbol']: stock['id'] for stock in symbols_instance}
        today_stocks = Nse(by_trade_date).data()

        stocks_history = []

        for stock in today_stocks:
            stock_id = symbols.get(stock['SYMBOL'])
            if not stock_id:
                stock_instance = Stock.objects.create(symbol=stock['SYMBOL'], isin=stock['ISIN'])
                stock_id = stock_instance.id

            stocks_history.append(self.model(stock_id=stock_id,
                                             open=stock['OPEN'], high=stock['HIGH'], low=stock['LOW'],
                                             close=stock['CLOSE'], last=stock['LAST'], prev_close=stock['PREVCLOSE'],
                                             total_traded_qty=stock['TOTTRDQTY'], total_traded_value=stock['TOTTRDVAL'],
                                             trade_date=stock['TRADEDDATE'], total_trades=stock['TOTALTRADES']))

        if stocks_history:
            StockHistory.objects.bulk_create(stocks_history)
            logger.info("Stocks downloaded for %s" % by_trade_date)
        else:
            # for cron logs
            logger.info("[%s] No data found on NSE" % datetime.now())


class StockHistory(models.Model):
    stock = models.ForeignKey(Stock, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    trade_date = models.DateField(verbose_name="Traded date", db_index=True)
    open = models.FloatField(verbose_name="Open price")
    high = models.FloatField(verbose_name="High price")
    low = models.FloatField(verbose_name="Low price")
    close = models.FloatField(verbose_name="Close price")
    last = models.FloatField(verbose_name="Last price")
    prev_close = models.FloatField(verbose_name="Previous Close price")
    total_traded_qty = models.IntegerField(verbose_name="Total Traded quantity")
    total_traded_value = models.FloatField(verbose_name="Total Traded value")
    total_trades = models.IntegerField(verbose_name="Total Trades")

    def __str__(self):
        return '%d - %s' % (self.id, self.stock.symbol)

    objects = StockHistoryManager()

    class Meta:
        ordering = ('trade_date',)


class StockOrder(models.Model):
    BOUGHT = 1
    SOLD = 2
    order_choices = ((BOUGHT, 'BOUGHT'),
                     (SOLD, 'SOLD'))

    stock_history = models.ForeignKey(StockHistory, db_index=True, unique=True)
    status = models.PositiveSmallIntegerField(choices=order_choices, default=1)
    sold_at = models.DateTimeField(verbose_name='Sold at', db_index=True, null=True)
    sold_price = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Order ID: %d - Stock: %s' % (self.id, self.stock_history.stock.symbol)
