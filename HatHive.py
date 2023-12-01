import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import messagebox, scrolledtext, Entry, Button, Label, LabelFrame, Frame
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib

TABLES = {
    'customers': (
        "CREATE TABLE `customers` ("
        "  `customer_id` int NOT NULL AUTO_INCREMENT,"
        "  `name` varchar(255) NOT NULL,"
        "  `DOB` date NOT NULL,"
        "  `email` varchar(255) NOT NULL,"
        "  `contact_info` varchar(255) NOT NULL,"
        "  `address` varchar(255) NOT NULL,"
        "  PRIMARY KEY (`customer_id`)"
        ") ENGINE=InnoDB"
    ),
    'orders': (
        "CREATE TABLE `orders` ("
        "  `order_id` int NOT NULL AUTO_INCREMENT,"
        "  `customer_id` int NOT NULL,"
        "  `hat_id` int NOT NULL,"
        "  `date` date NOT NULL,"
        "  `quantity` int NOT NULL,"
        "  PRIMARY KEY (`order_id`),"
        "  FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`hat_id`) REFERENCES `hats` (`hat_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    ),
    'hats': (
        "CREATE TABLE `hats` ("
        "  `hat_id` int NOT NULL AUTO_INCREMENT,"
        "  `brand_id` int NOT NULL,"
        "  `brand_name` varchar(255) NOT NULL,"
        "  `style` varchar(255) NOT NULL,"
        "  `size` int NOT NULL,"
        "  `quantity` int NOT NULL,"
        "  `price` decimal(10,2) NOT NULL,"
        "  PRIMARY KEY (`hat_id`)"
        ") ENGINE=InnoDB"
    ),
    'bills': (
        "CREATE TABLE `bills` ("
        "  `bill_id` int NOT NULL AUTO_INCREMENT,"
        "  `order_id` int NOT NULL,"
        "  `tax` decimal(10,2) NOT NULL,"
        "  `price` decimal(10,2) NOT NULL,"
        "  `payment_method` varchar(255) NOT NULL,"
        "  `payment_status` varchar(255),"
        "  `transaction_id` varchar(255),"
        "  PRIMARY KEY (`bill_id`),"
        "  FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    ),
    'delivery': (
        "CREATE TABLE `delivery` ("
        "  `delivery_id` int NOT NULL AUTO_INCREMENT,"
        "  `order_id` int NOT NULL,"
        "  `arrival_date` date NOT NULL,"
        "  PRIMARY KEY (`delivery_id`),"
        "  FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )
}


class DatabaseManager:
    def __init__(self, host, user, password, db_name):
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db_name
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print(f"Connected to MySQL Server version {db_info}")
                cursor = self.connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
                cursor.execute(f"USE {self.db_name}")
                print(f"You're connected to database: {self.db_name}")
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")

    def ensure_table_columns(self):
        # Ensure the bills table has all the required columns
        alter_queries = [
            "ALTER TABLE bills ADD COLUMN payment_status VARCHAR(255)",
            "ALTER TABLE bills ADD COLUMN transaction_id VARCHAR(255)"
        ]

        with self.connection.cursor() as cursor:
            for query in alter_queries:
                try:
                    cursor.execute(query)
                    self.connection.commit()
                except Error as e:
                    if e.errno == mysql.connector.errorcode.ER_DUP_FIELDNAME:
                        print("Column already exists: ", e)
                    else:
                        raise

    def create_tables(self):
        self.ensure_table_columns()  # Call this method before creating tables
        cursor = self.connection.cursor()
        for table_name, ddl in TABLES.items():
            try:
                print(f"Creating table {table_name}: ", end='')
                cursor.execute(ddl)
            except mysql.connector.Error as err:
                if err.errno == mysql.connector.errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
            else:
                print("OK")
        cursor.close()

    def execute_query(self, query, params=None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, params or ())
                if query.strip().lower().startswith("select"):
                    return cursor.fetchall()  # Return the result for 'select' queries
                self.connection.commit()  # Commit changes for 'insert', 'update', 'delete'
                return None  # For non-select queries, we don't need to return anything
            except Error as e:
                print(f"An error occurred: {e}")
                raise

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection is closed")


# Utility function to validate the date format
def validate_date(date_text):
    try:
        if date_text != datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        return True
    except ValueError:
        return False


class HatHiveApp:
    def __init__(self, master):
        self.master = master
        self.master.title("HatHive: Hat Sales Management System")
        self.db_manager = None
        self.setup_gui()

    def setup_gui(self):
        self.master.geometry('1024x768')

        # Left panel for inputs and actions
        input_frame = LabelFrame(self.master, text="Database Connection", padx=5, pady=5)
        input_frame.pack(side="left", padx=10, pady=10, fill="both")

        Label(input_frame, text="Host:").grid(row=0, column=0, sticky="w")
        self.host_entry = Entry(input_frame)
        self.host_entry.grid(row=0, column=1, sticky="ew")

        Label(input_frame, text="User:").grid(row=1, column=0, sticky="w")
        self.user_entry = Entry(input_frame)
        self.user_entry.grid(row=1, column=1, sticky="ew")

        Label(input_frame, text="Password:").grid(row=2, column=0, sticky="w")
        self.password_entry = Entry(input_frame, show="*")
        self.password_entry.grid(row=2, column=1, sticky="ew")

        connect_button = Button(input_frame, text="Connect", command=self.connect_to_database)
        connect_button.grid(row=3, column=1, sticky="ew", pady=5)

        # Right panel for displaying results
        output_frame = Frame(self.master, padx=5, pady=5)
        output_frame.pack(side="right", expand=True, fill="both")
        self.query_result = scrolledtext.ScrolledText(output_frame, height=20)
        self.query_result.pack(fill="both", expand=True)

        # Customer related actions
        customer_action_frame = Frame(input_frame, padx=5, pady=5)
        customer_action_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
        Button(customer_action_frame, text="View Customers", command=self.view_customers).pack(side="left", padx=5)
        Button(customer_action_frame, text="Add Customer", command=self.add_customer).pack(side="left", padx=5)

        # Hat related actions
        hat_action_frame = Frame(input_frame, padx=5, pady=5)
        hat_action_frame.grid(row=5, column=0, columnspan=2, sticky="ew")
        Button(hat_action_frame, text="View Hats", command=self.view_hats).pack(side="left", padx=5)
        Button(hat_action_frame, text="Add Hat", command=self.add_hat).pack(side="left", padx=5)

        # Order related actions
        order_action_frame = Frame(input_frame, padx=5, pady=5)
        order_action_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
        Button(order_action_frame, text="Place Order", command=self.add_order).pack(side="left", padx=5)
        Button(order_action_frame, text="View Orders", command=self.view_orders).pack(side="left", padx=5)

        # Delivery related actions
        delivery_action_frame = Frame(input_frame, padx=5, pady=5)
        delivery_action_frame.grid(row=8, column=0, columnspan=2, sticky="ew")
        Button(delivery_action_frame, text="View Deliveries", command=self.view_deliveries).pack(side="left", padx=5)

        # Billing actions
        billing_action_frame = Frame(input_frame, padx=5, pady=5)
        billing_action_frame.grid(row=9, column=0, columnspan=2, sticky="ew")
        Button(billing_action_frame, text="View Bills", command=self.view_bills).pack(side="left", padx=5)

        # Application-wide actions
        app_action_frame = Frame(input_frame, padx=5, pady=5)
        app_action_frame.grid(row=7, column=0, columnspan=2, sticky="ew")
        Button(app_action_frame, text="Clear All Data", command=self.clear_all_data).pack(side="left", padx=5)
        Button(app_action_frame, text="Exit", command=self.on_closing).pack(side="left", padx=5)

    def connect_to_database(self):
        host = self.host_entry.get()
        user = self.user_entry.get()
        password = self.password_entry.get()
        try:
            self.db_manager = DatabaseManager(host, user, password, 'HatHive')
            self.db_manager.connect()
            self.db_manager.create_tables()  # Ensure tables and columns are created after connection
            messagebox.showinfo("Connection", "Connected to the database successfully.")
        except Error as e:
            messagebox.showerror("Database Connection", f"An error occurred: {e}")

    # Function to fetch and display customers from the database
    def view_customers(self):
        query = "SELECT * FROM customers"
        try:
            records = self.db_manager.execute_query(query)
            self.query_result.delete('1.0', tk.END)

            # Dynamically compute column widths
            col_widths = [max(len(str(row[i])) for row in records) for i in range(len(records[0]))]

            headers = ["ID", "Name", "DOB", "Email", "Contact", "Address"]
            header_string = "".join(h.ljust(col_widths[i] + 2) for i, h in enumerate(headers))

            # Add headers
            self.query_result.insert(tk.END, header_string + "\n")
            self.query_result.insert(tk.END, "-" * len(header_string) + "\n")

            for record in records:
                formatted_record = "".join(str(field).ljust(col_widths[i] + 2) for i, field in enumerate(record))
                self.query_result.insert(tk.END, formatted_record + "\n")
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    # Function to add a new customer to the database
    def add_customer(self):
        # Open a new window to input new customer details
        add_window = tk.Toplevel(self.master)
        add_window.title("Add New Customer")

        Label(add_window, text="Name:").grid(row=0, column=0)
        name_entry = Entry(add_window)
        name_entry.grid(row=0, column=1)

        Label(add_window, text="Date of Birth (YYYY-MM-DD):").grid(row=1, column=0)
        dob_entry = Entry(add_window)
        dob_entry.grid(row=1, column=1)

        Label(add_window, text="Email:").grid(row=2, column=0)
        email_entry = Entry(add_window)
        email_entry.grid(row=2, column=1)

        Label(add_window, text="Contact Info:").grid(row=3, column=0)
        contact_info_entry = Entry(add_window)
        contact_info_entry.grid(row=3, column=1)

        Label(add_window, text="Address:").grid(row=4, column=0)
        address_entry = Entry(add_window)
        address_entry.grid(row=4, column=1)

        submit_button = Button(add_window, text="Submit", command=lambda: self.submit_new_customer(
            name_entry.get(),
            dob_entry.get(),
            email_entry.get(),
            contact_info_entry.get(),
            address_entry.get(),
            add_window
        ))
        submit_button.grid(row=5, column=1, pady=5)

    def submit_new_customer(self, name, dob, email, contact_info, address, window):
        if not all([name, dob, email, contact_info, address]):
            messagebox.showwarning("Warning", "All fields are required to add a new customer.")
            return

        if not validate_date(dob):
            messagebox.showerror("Invalid Date", "The Date of Birth is in an incorrect format. Please use YYYY-MM-DD.")
            return

        query = "INSERT INTO customers (name, DOB, email, contact_info, address) VALUES (%s, %s, %s, %s, %s)"
        try:
            self.db_manager.execute_query(query, (name, dob, email, contact_info, address))
            messagebox.showinfo("Success", "New customer added successfully.")
            window.destroy()  # Close the add new customer window
            self.view_customers()  # Refresh the customer view
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def view_hats(self):
        query = "SELECT * FROM hats"
        try:
            records = self.db_manager.execute_query(query)
            self.query_result.delete('1.0', tk.END)

            # Dynamically compute column widths
            col_widths = [max(len(str(row[i])) for row in records) for i in range(len(records[0]))]

            headers = ["ID", "Brand ID", "Brand Name", "Style", "Size", "Quantity"]
            header_string = "".join(h.ljust(col_widths[i] + 2) for i, h in enumerate(headers))

            # Add headers
            self.query_result.insert(tk.END, header_string + "\n")
            self.query_result.insert(tk.END, "-" * len(header_string) + "\n")

            for record in records:
                formatted_record = "".join(str(field).ljust(col_widths[i] + 2) for i, field in enumerate(record))
                self.query_result.insert(tk.END, formatted_record + "\n")
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def add_hat(self):
        add_hat_window = tk.Toplevel(self.master)
        add_hat_window.title("Add New Hat")

        Label(add_hat_window, text="Brand ID:").grid(row=0, column=0)
        brand_id_entry = Entry(add_hat_window)
        brand_id_entry.grid(row=0, column=1)

        Label(add_hat_window, text="Brand Name:").grid(row=1, column=0)
        brand_name_entry = Entry(add_hat_window)
        brand_name_entry.grid(row=1, column=1)

        Label(add_hat_window, text="Style:").grid(row=2, column=0)
        style_entry = Entry(add_hat_window)
        style_entry.grid(row=2, column=1)

        Label(add_hat_window, text="Size:").grid(row=3, column=0)
        size_entry = Entry(add_hat_window)
        size_entry.grid(row=3, column=1)

        Label(add_hat_window, text="Quantity:").grid(row=4, column=0)
        quantity_entry = Entry(add_hat_window)
        quantity_entry.grid(row=4, column=1)

        submit_button = Button(add_hat_window, text="Submit", command=lambda: self.submit_new_hat(
            brand_id_entry.get(),
            brand_name_entry.get(),
            style_entry.get(),
            size_entry.get(),
            quantity_entry.get(),
            add_hat_window
        ))
        submit_button.grid(row=5, column=1, pady=5)

    def submit_new_hat(self, brand_id, brand_name, style, size, quantity, window):
        if not all([brand_id, brand_name, style, size, quantity]):
            messagebox.showwarning("Warning", "All fields are required to add a new hat.")
            return

        # Additional validation can go here (e.g., check if size is an integer)

        query = "INSERT INTO hats (brand_id, brand_name, style, size, quantity) VALUES (%s, %s, %s, %s, %s)"
        try:
            self.db_manager.execute_query(query, (brand_id, brand_name, style, size, quantity))
            messagebox.showinfo("Success", "New hat added successfully.")
            window.destroy()
            self.view_hats()  # Optionally refresh the hats view
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def add_order(self):
        add_order_window = tk.Toplevel(self.master)
        add_order_window.title("Place New Order")

        Label(add_order_window, text="Customer ID:").grid(row=0, column=0)
        customer_id_entry = Entry(add_order_window)
        customer_id_entry.grid(row=0, column=1)

        Label(add_order_window, text="Hat ID:").grid(row=1, column=0)
        hat_id_entry = Entry(add_order_window)
        hat_id_entry.grid(row=1, column=1)

        Label(add_order_window, text="Order Date (YYYY-MM-DD):").grid(row=2, column=0)
        order_date_entry = Entry(add_order_window)
        order_date_entry.grid(row=2, column=1)

        Label(add_order_window, text="Quantity:").grid(row=3, column=0)
        quantity_entry = Entry(add_order_window)
        quantity_entry.grid(row=3, column=1)

        submit_button = Button(add_order_window, text="Submit", command=lambda: self.submit_new_order(
            customer_id_entry.get(),
            hat_id_entry.get(),
            order_date_entry.get(),
            quantity_entry.get(),
            add_order_window
        ))
        submit_button.grid(row=4, column=1, pady=5)

    def submit_new_order(self, customer_id, hat_id, order_date, quantity, window):
        if not all([customer_id, hat_id, order_date, quantity]):
            messagebox.showwarning("Warning", "All fields are required to place an order.")
            return

        if not validate_date(order_date):
            messagebox.showerror("Invalid Date", "The order date is in an incorrect format. Please use YYYY-MM-DD.")
            return

        try:
            # Check if customer ID exists
            customer_query = "SELECT * FROM customers WHERE customer_id = %s"
            customer_result = self.db_manager.execute_query(customer_query, (customer_id,))
            if not customer_result:
                messagebox.showerror("Error", "Customer ID does not exist.")
                return

            # Check if hat ID exists and if there's enough stock
            hat_query = "SELECT quantity FROM hats WHERE hat_id = %s"
            hat_result = self.db_manager.execute_query(hat_query, (hat_id,))
            if not hat_result:
                messagebox.showerror("Error", "Hat ID does not exist.")
                return

            available_quantity = hat_result[0][0]
            if int(quantity) > available_quantity:
                messagebox.showerror("Error", "Not enough stock for the hat.")
                return

            # All checks passed, place the order
            insert_order_query = "INSERT INTO orders (customer_id, hat_id, date, quantity) VALUES (%s, %s, %s, %s)"
            self.db_manager.execute_query(insert_order_query, (customer_id, hat_id, order_date, quantity))

            # Update hats quantity
            new_quantity = available_quantity - int(quantity)
            update_hat_query = "UPDATE hats SET quantity = %s WHERE hat_id = %s"
            self.db_manager.execute_query(update_hat_query, (new_quantity, hat_id))

            # Get the last inserted order_id for the delivery
            last_order_id_query = "SELECT LAST_INSERT_ID();"
            last_order_id_result = self.db_manager.execute_query(last_order_id_query)
            last_order_id = last_order_id_result[0][0]

            # Calculate the estimated arrival date and insert into delivery
            order_date_obj = datetime.strptime(order_date, '%Y-%m-%d')
            estimated_arrival = order_date_obj + timedelta(days=5)
            insert_delivery_query = "INSERT INTO delivery (order_id, arrival_date) VALUES (%s, %s)"
            self.db_manager.execute_query(insert_delivery_query, (last_order_id, estimated_arrival))

            messagebox.showinfo("Success", "Order placed and delivery scheduled successfully.")

            # Get the price for the hat
            hat_price = self.get_hat_price(hat_id)  # You'll implement this method

            # Calculate the total price and tax for the order
            # Ensure quantity is an integer
            quantity = int(quantity)

            # Now the multiplication should work
            total_price = quantity * hat_price

            tax = self.calculate_tax(total_price)  # You'll implement this method
            payment_method = "Credit Card"  # Example payment method

            # Get the last order ID to link the bill to the correct order
            last_order_id = self.get_last_inserted_id()

            # Create the bill
            self.create_bill(last_order_id, tax, total_price, payment_method)

            # Proceed to payment
            self.process_payment(last_order_id, total_price + tax)  # You'll implement this method

            messagebox.showinfo("Success", "Order placed, bill created, and payment processed successfully.")
            window.destroy()

        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

        # Implement the get_hat_price method to retrieve the price of a hat from the database

    def get_hat_price(self, hat_id):
        query = "SELECT price FROM hats WHERE hat_id = %s"
        result = self.db_manager.execute_query(query, (hat_id,))
        if result:
            return Decimal(result[0][0])
        else:
            raise Exception("Hat not found.")

        # Implement the calculate_tax method to calculate the tax based on the total price

    def calculate_tax(self, total_price):
        tax_rate = Decimal('0.07')  # Example tax rate of 7%
        return total_price * tax_rate

        # Implement the get_last_inserted_id method to get the ID of the last inserted record

    def get_last_inserted_id(self):
        last_order_id_query = "SELECT LAST_INSERT_ID();"
        last_order_id_result = self.db_manager.execute_query(last_order_id_query)
        return last_order_id_result[0][0]

        # Implement the create_bill method to create a bill record in the database

    def create_bill(self, order_id, tax, total_price, payment_method):
        insert_bill_query = """
          INSERT INTO bills (order_id, tax, price, payment_method) VALUES (%s, %s, %s, %s)
          """
        self.db_manager.execute_query(insert_bill_query, (order_id, tax, total_price, payment_method))

    # Implement the process_payment method to handle payment processing
    def process_payment(self, order_id, amount_due):
        # In a real system, you would now interact with a payment processor/gateway
        # For this example, we'll simulate a successful payment by updating the bill status

        # Simulate generating a secure hash for the transaction (in reality, use secure methods)
        transaction_id = hashlib.sha256(f"{order_id}{amount_due}".encode()).hexdigest()

        update_payment_query = """
        UPDATE bills SET payment_status = %s, transaction_id = %s WHERE order_id = %s
        """
        self.db_manager.execute_query(update_payment_query, ('Paid', transaction_id, order_id))

    def view_deliveries(self):
        self.query_result.delete('1.0', tk.END)  # Clear existing content
        query = "SELECT delivery.delivery_id, orders.order_id, delivery.arrival_date FROM delivery JOIN orders ON delivery.order_id = orders.order_id"
        try:
            records = self.db_manager.execute_query(query)
            print("Fetched records:", records)  # Debugging line

            if not records:
                self.query_result.insert(tk.END, "No delivery records found.\n")
                return

            # Dynamically compute column widths
            col_widths = [max(len(str(row[i])) for row in records) for i in range(len(records[0]))]

            headers = ["Delivery ID", "Order ID", "Arrival Date"]
            header_string = "".join(h.ljust(col_widths[i] + 2) for i, h in enumerate(headers))

            # Add headers
            self.query_result.insert(tk.END, header_string + "\n")
            self.query_result.insert(tk.END, "-" * len(header_string) + "\n")

            for record in records:
                formatted_record = "".join(str(field).ljust(col_widths[i] + 2) for i, field in enumerate(record))
                self.query_result.insert(tk.END, formatted_record + "\n")
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def view_orders(self):
        query = "SELECT * FROM orders"
        try:
            records = self.db_manager.execute_query(query)
            self.query_result.delete('1.0', tk.END)

            # Dynamically compute column widths
            col_widths = [max(len(str(row[i])) for row in records) for i in range(len(records[0]))]

            headers = ["Order ID", "Customer ID", "Hat ID", "Order Date", "Quantity"]
            header_string = "".join(h.ljust(col_widths[i] + 2) for i, h in enumerate(headers))

            # Add headers
            self.query_result.insert(tk.END, header_string + "\n")
            self.query_result.insert(tk.END, "-" * len(header_string) + "\n")

            for record in records:
                formatted_record = "".join(str(field).ljust(col_widths[i] + 2) for i, field in enumerate(record))
                self.query_result.insert(tk.END, formatted_record + "\n")
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def clear_all_data(self):
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete all data?")
        if confirm:
            try:
                self.db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 0;")  # Disable foreign key checks
                self.db_manager.execute_query("TRUNCATE TABLE bills;")
                self.db_manager.execute_query("TRUNCATE TABLE delivery;")
                self.db_manager.execute_query("TRUNCATE TABLE orders;")
                self.db_manager.execute_query("TRUNCATE TABLE hats;")
                self.db_manager.execute_query("TRUNCATE TABLE customers;")
                self.db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 1;")  # Re-enable foreign key checks
                messagebox.showinfo("Success", "All data has been deleted.")
            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred: {e}")

    def view_bills(self):
        self.query_result.delete('1.0', tk.END)  # Clear existing content in the text box
        query = "SELECT bill_id, order_id, tax, price, payment_method, payment_status FROM bills"
        try:
            records = self.db_manager.execute_query(query)

            if not records:
                self.query_result.insert(tk.END, "No billing records found.\n")
                return

            # Dynamically compute column widths
            col_widths = [max(len(str(row[i])) for row in records) for i in range(len(records[0]))]

            headers = ["Bill ID", "Order ID", "Tax", "Price", "Payment Method", "Payment Status"]
            header_string = "".join(h.ljust(col_widths[i] + 2) for i, h in enumerate(headers))

            # Add headers
            self.query_result.insert(tk.END, header_string + "\n")
            self.query_result.insert(tk.END, "-" * len(header_string) + "\n")

            for record in records:
                formatted_record = "".join(str(field).ljust(col_widths[i] + 2) for i, field in enumerate(record))
                self.query_result.insert(tk.END, formatted_record + "\n")
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def on_closing(self):
        if self.db_manager:
            self.db_manager.close()
        self.master.destroy()


def main():
    root = tk.Tk()
    app = HatHiveApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
