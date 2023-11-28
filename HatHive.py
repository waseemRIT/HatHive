import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import messagebox, scrolledtext, Entry, Button, Label, LabelFrame, Frame
from datetime import datetime

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
        "  PRIMARY KEY (`hat_id`)"
        ") ENGINE=InnoDB"
    ),
    'bills': (
        "CREATE TABLE `bills` ("
        "  `bill_id` int NOT NULL AUTO_INCREMENT,"
        "  `order_id` int NOT NULL,"
        "  `tax` int NOT NULL,"
        "  `price` int NOT NULL,"
        "  `payment_method` varchar(255) NOT NULL,"
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

    def create_tables(self):
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

        # Action buttons for database operations
        action_frame = Frame(input_frame, padx=5, pady=5)
        action_frame.grid(row=4, column=0, columnspan=2, sticky="ew")

        Button(action_frame, text="View Customers", command=self.view_customers).pack(side="left", padx=5)
        Button(action_frame, text="Add Customer", command=self.add_customer).pack(side="left", padx=5)
        view_hats_button = Button(action_frame, text="View Hats", command=self.view_hats)
        view_hats_button.pack(side="left", padx=5)

        add_hat_button = Button(action_frame, text="Add Hat", command=self.add_hat)
        add_hat_button.pack(side="left", padx=5)

        place_order_button = Button(action_frame, text="Place Order", command=self.add_order)
        place_order_button.pack(side="left", padx=5)

        view_orders_button = Button(action_frame, text="View Orders", command=self.view_orders)
        view_orders_button.pack(side="left", padx=5)

        exit_button = Button(action_frame, text="Exit", command=self.on_closing)
        exit_button.pack(side="left", padx=5)

    def connect_to_database(self):
        host = self.host_entry.get()
        user = self.user_entry.get()
        password = self.password_entry.get()
        try:
            self.db_manager = DatabaseManager(host, user, password, 'HatHive')
            self.db_manager.connect()
            self.db_manager.create_tables()  # Create tables after connection
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

            # All checks passed, place the order and update the stock
            insert_order_query = "INSERT INTO orders (customer_id, hat_id, date, quantity) VALUES (%s, %s, %s, %s)"
            self.db_manager.execute_query(insert_order_query, (customer_id, hat_id, order_date, quantity))

            # Update hats quantity
            new_quantity = available_quantity - int(quantity)
            update_hat_query = "UPDATE hats SET quantity = %s WHERE hat_id = %s"
            self.db_manager.execute_query(update_hat_query, (new_quantity, hat_id))

            messagebox.showinfo("Success", "Order placed successfully.")
            window.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    # Add this method to the HatHiveApp class

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
