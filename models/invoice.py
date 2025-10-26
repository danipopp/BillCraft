class Invoice:
    def __init__(self, customer_id, date, total):
        self.customer_id = customer_id
        self.date = date
        self.total = total
        self.lines = []  # List of InvoiceLine objects

    def add_line(self, line):
        self.lines.append(line)
