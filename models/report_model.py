class RevenueReport:
    def __init__(self, report_id: str, from_date: str, to_date: str, report_type: str, 
                 total_revenue: float = 0.0, total_orders: int = 0, 
                 avg_order_value: float = 0.0, top_performers: list = None, chart_data: dict = None):
        self.reportID = report_id
        self.fromDate = from_date
        self.toDate = to_date
        self.reportType = report_type
        self.totalRevenue = total_revenue
        self.totalOrders = total_orders
        self.avgOrderValue = avg_order_value
        self.topPerformers = top_performers if top_performers else []
        self.chartData = chart_data if chart_data else {"labels": [], "values": []}