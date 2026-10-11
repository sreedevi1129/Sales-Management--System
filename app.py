import streamlit as st
import mysql.connector
import pandas as pd
st.set_page_config(layout="wide")
connection = mysql.connector.connect(host="localhost",
    user="root",
    password="root",
    database="sales_management_system"
    )
if "user" not in st.session_state:
    st.session_state.user=None
if st.session_state.user is None:
    st.title("Sales Management System")
    username = st.text_input("Username")
    password = st.text_input("Password", type = "password")


    if st.button("Login"):
       cursor = connection.cursor()
       query="SELECT * FROM users WHERE username=%s AND password=%s"
       cursor.execute(query,(username,password))
       result = cursor.fetchone()
       if result:
           st.session_state.user = result
           st.rerun()
       else:
           st.error("Invalid username or password")
if st.session_state.user is not None:
    result =st.session_state.user
    st.sidebar.title("🧭 Navigation")
    menu = st.sidebar.radio(
        "Go to",
        [
            "📊Dashboard & Reports",
            "✚ Data Entry Workspace",
            "📂Advanced SQL Engine"
            ]
    )
    st.sidebar.divider()

    st.sidebar.write("👤User:",result[1])
    st.sidebar.write("🔑Role:",result[4])

    st.sidebar.divider()
    if st.sidebar.button("🔐Log Out"):
        st.session_state.user=None
        st.rerun()

    st.write("Role:",result[4])
    if menu=="📊Dashboard & Reports":
        st.subheader("🔍Filter Controls")
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            cursor=connection.cursor()
            cursor.execute("SELECT branch_id FROM branches ORDER BY branch_id")
            branch_ids=[row[0]for row in cursor.fetchall()]
            selected_branch=st.selectbox("Branch ID",["All"]+branch_ids)
        with col2:
            cursor.execute("SELECT DISTINCT product_name FROM customer_sales")
            product_names=[row[0]for row in cursor.fetchall()]
            product=st.selectbox("Select Product",["All"]+product_names)
        with col3:
            start_date = st.date_input("Start Date")
        with col4:
            end_date = st.date_input("End Date")
        if result[4] == "Super Admin":
            sales_cursor = connection.cursor()
            sales_query= "SELECT * FROM customer_sales WHERE date BETWEEN %s AND %s"
            params=[start_date,end_date]
            if selected_branch !="All":
                sales_query += "AND branch_id=%s"
                params.append(selected_branch)
            if product != "All":
                sales_query+= "AND product_name =%s"
                params.append(product)

            sales_cursor.execute(sales_query,tuple(params))
              
        else:
            sales_cursor = connection.cursor()
            if product =="All":
              sales_query= """SELECT * FROM customer_sales WHERE branch_id = %s AND date BETWEEN %s AND %s"""
              sales_cursor.execute(sales_query,(result[3],start_date,end_date))
            else:
                sales_query= """SELECT * FROM customer_sales WHERE branch_id = %s AND product_name=%s AND date BETWEEN %s AND %s"""
                sales_cursor.execute(sales_query,(result[3],product,start_date,end_date))

        sales = sales_cursor.fetchall()
        columns = [column[0] for column in sales_cursor.description]
        df= pd.DataFrame(sales,columns=columns)
        st.dataframe(df)
        st.subheader("💵 Financial Summary")
        total_gross = df["gross_sales"].sum()
        total_received=df["received_amount"].sum()
        total_pending=df["pending_amount"].sum()
        if total_gross >0:
            collection_percentage =(total_received/total_gross)*100
        else:
            collection_percentage =0
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            st.metric("💰Total sales (Gross)",f"₹{total_gross:,.2f}")
        with col2:
            st.metric("💸 Total Received",f"₹{total_received:,.2f}")
        with col3:
            st.metric("⌛Total Pending",f"₹{total_pending:,.2f}")
        with col4:
            st.metric("📊 Collection %",f"₹{collection_percentage:.1f}%")
      
    if menu=="✚ Data Entry Workspace": 
          st.title ("📝 Operations Record Creator")
          tab1, tab2 =st.tabs([
              "Add New Sales Entry",
              "Payment Split Details"
    ])
          with tab1:
              st.markdown("___")
              st.subheader("New Sale Generation")
              customer_name = st.text_input("Student Name")
              mobile_number = st.text_input("Mobile Number")
              product_cursor =connection.cursor()
              product_cursor.execute("SELECT DISTINCT product_name FROM customer_sales ORDER BY product_name")
              product_list=[row[0] for row in product_cursor.fetchall()]
              new_product_name=st.selectbox("Product",product_list)
              gross_sales = st.number_input("Gross Sales",min_value =0)
              sale_date = st.date_input("Sale Date")
              status = st.selectbox("Status",["open","close"])
              if result[4]=="Super Admin":
                  branch_cursor =connection.cursor()
                  branch_cursor.execute("SELECT branch_id,branch_name FROM branches ORDER BY branch_id")
                  branch_rows=branch_cursor.fetchall()
                  branch_options={row[1]:row[0] for row in branch_rows}
                  selected_branch =st.selectbox(
                      "Select Target Branch",
                      list(branch_options.keys())
                      )
                  branch_id=branch_options[selected_branch]

              else:
                  branch_id=result[3]

              if st.button("Add Sale"):
                  sales_cursor = connection.cursor()
                  sales_query = """ INSERT INTO customer_sales(branch_id,date,customer_name,mobile_number,product_name,gross_sales,status)
                  VALUES (%s,%s,%s,%s,%s,%s,%s)"""
                  sales_cursor.execute(sales_query,(branch_id,sale_date,customer_name,mobile_number,new_product_name,gross_sales,status))
                  connection.commit()
                  st.success("Sale added successfully")
          with tab2:
              st.markdown("___")
              st.subheader("Payment splits Details")
              payment_sale_id = st.number_input("Sale ID",min_value=1,step=1)
              payment_date =st.date_input("Payment Date")
              amount_paid = st.number_input("Amount Paid",min_value=0.00,step=100.0)
              payment_method = st.selectbox("Payment Method",["Cash","UPI","Card"])
              if st.button("Add Payment"):
                  if amount_paid <=0:
                      st.error("Amount paid must be greater than 0")
                  else:
                      payment_cursor = connection.cursor()
                      payment_query="""INSERT INTO payment_splits(sale_id,payment_date,amount_paid,payment_method)
                      VALUES (%s,%s,%s,%s)"""
                      payment_cursor.execute(payment_query,(payment_sale_id,payment_date,amount_paid,payment_method))
                      connection.commit()
                      st.success("Payment added successfully")

    if menu == "📂Advanced SQL Engine":
          st.title("📂Advanced SQL Engine")
          questions={
              "1. Retrieve all customer sales records":
                  "SELECT * FROM customer_sales",

              "2. Retrieve all branches":
                  "SELECT * FROM branches",

              "3. Retrieve all payment records":
                  "SELECT * FROM payment_splits",

              "4. Display sales with Open status":
                  "SELECT * FROM customer_sales WHERE status = 'open'",

              "5. Total gross sales":
                  "SELECT SUM(gross_sales) AS total_gross_sales FROM customer_sales",

              "6. Total received amount":
                  "SELECT SUM(received_amount) AS total_received_amount FROM customer_sales",

              "7. Total pending amount":
                  "SELECT SUM(pending_amount) AS total_pending_amount FROM customer_sales",

              "8. Number of sales per branch":
                  """SELECT branch_id, COUNT(*) AS total_sales
                     FROM customer_sales
                     GROUP BY branch_id""",

              "9. Sales with branch name":
                  """SELECT cs.*, b.branch_name
                     FROM customer_sales cs
                     JOIN branches b ON cs.branch_id = b.branch_id""",

              "10. Sales with total payments received":
                   """SELECT cs.sale_id, cs.customer_name, cs.gross_sales,
                      COALESCE(SUM(ps.amount_paid), 0) AS total_payments
                      FROM customer_sales cs
                      LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
                      GROUP BY cs.sale_id, cs.customer_name, cs.gross_sales""",

              "11. Sales with payment method":
                   """SELECT cs.sale_id, cs.customer_name, ps.payment_method,
                      ps.amount_paid, ps.payment_date
                      FROM customer_sales cs
                      JOIN payment_splits ps ON cs.sale_id = ps.sale_id""",

              "12. Sales with branch admin name":
                   """SELECT cs.*, b.branch_admin_name
                      FROM customer_sales cs
                      JOIN branches b ON cs.branch_id = b.branch_id""",

              "13. Sales with pending amount above 5000":
                   """SELECT * FROM customer_sales
                      WHERE pending_amount > 5000""",

              "14. Top 3 highest gross sales":
                   """SELECT * FROM customer_sales
                      ORDER BY gross_sales DESC
                      LIMIT 3""",

              "15. Branch with highest gross sales":
                   """SELECT b.branch_id, b.branch_name,
                      SUM(cs.gross_sales) AS total_gross_sales
                      FROM branches b
                      JOIN customer_sales cs ON b.branch_id = cs.branch_id
                      GROUP BY b.branch_id, b.branch_name
                      ORDER BY total_gross_sales DESC
                      LIMIT 1"""
          }
          selected_question=st.selectbox(
              "Select SQL Question",
              list(questions.keys())
          )

          st.code(questions[selected_question],language ="sql")
          if st.button("Run Query"):
              try:
                  sql_cursor = connection.cursor()
                  query =questions[selected_question]
                  if result[4]=="Super Admin":
                      sql_cursor.execute(query)
                  else:
                      branch_id = result[3]
                      if selected_question == "1. Retrieve all customer sales records":
                         sql_cursor.execute(
                              "SELECT * FROM customer_sales WHERE branch_id = %s",
                               (branch_id,)
                          )
                      elif selected_question == "2. Retrieve all branches":
                            sql_cursor.execute(
                                "SELECT * FROM branches WHERE branch_id = %s",
                                (branch_id,)
                          )
                      elif selected_question == "3. Retrieve all payment records":
                            sql_cursor.execute(
                                """SELECT ps.* FROM payment_splits ps
                                    JOIN customer_sales cs ON ps.sale_id = cs.sale_id
                                    WHERE cs.branch_id = %s""",
                                    (branch_id,)
                          )
                      elif selected_question == "4. Display sales with Open status":
                            sql_cursor.execute(
                                """SELECT * FROM customer_sales
                                    WHERE status = 'open' AND branch_id = %s""",
                                    (branch_id,)
                          )
                      elif selected_question == "5. Total gross sales":
                            sql_cursor.execute(
                                  "SELECT SUM(gross_sales) AS total_gross_sales FROM customer_sales WHERE branch_id = %s",
                                  (branch_id,)
                          )
                      elif selected_question == "6. Total received amount":
                              sql_cursor.execute(
                                  "SELECT SUM(received_amount) AS total_received_amount FROM customer_sales WHERE branch_id = %s",
                                  (branch_id,)
                          )
                      elif selected_question == "7. Total pending amount":
                              sql_cursor.execute(
                                  "SELECT SUM(pending_amount) AS total_pending_amount FROM customer_sales WHERE branch_id = %s",
                                  (branch_id,)
                          )
                      elif selected_question == "8. Number of sales per branch":
                              sql_cursor.execute(
                                  """SELECT branch_id, COUNT(*) AS total_sales
                                     FROM customer_sales
                                     WHERE branch_id = %s
                                     GROUP BY branch_id""",
                                    (branch_id,)
                          )
                      elif selected_question == "9. Sales with branch name":
                                sql_cursor.execute(
                                    """SELECT cs.*, b.branch_name
                                       FROM customer_sales cs
                                        JOIN branches b ON cs.branch_id = b.branch_id
                                        WHERE cs.branch_id = %s""",
                                        (branch_id,)
              
                          )
                      elif selected_question == "10. Sales with total payments received":
                                sql_cursor.execute(
                                    """SELECT cs.sale_id, cs.customer_name, cs.gross_sales,
                                       COALESCE(SUM(ps.amount_paid), 0) AS total_payments
                                       FROM customer_sales cs
                                       LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
                                       WHERE cs.branch_id = %s
                                       GROUP BY cs.sale_id, cs.customer_name, cs.gross_sales""",
                                      (branch_id,)
                          )
                      elif selected_question == "11. Sales with payment method":
                                sql_cursor.execute(
                                    """SELECT cs.sale_id, cs.customer_name, ps.payment_method,
                                        ps.amount_paid, ps.payment_date
                                        FROM customer_sales cs
                                        JOIN payment_splits ps ON cs.sale_id = ps.sale_id
                                        WHERE cs.branch_id = %s""",
                                        (branch_id,)
                          )
                      elif selected_question == "12. Sales with branch admin name":
                                sql_cursor.execute(
                                    """SELECT cs.*, b.branch_admin_name
                                          FROM customer_sales cs
                                          JOIN branches b ON cs.branch_id = b.branch_id
                                          WHERE cs.branch_id = %s""",
                                          (branch_id,)
                          )
                      elif selected_question == "13. Sales with pending amount above 5000":
                                sql_cursor.execute(
                                    """SELECT * FROM customer_sales
                                          WHERE pending_amount > 5000 AND branch_id = %s""",
                                          (branch_id,)

                          )
                      elif selected_question == "14. Top 3 highest gross sales":
                                sql_cursor.execute(
                                    """SELECT * FROM customer_sales
                                        WHERE branch_id = %s
                                        ORDER BY gross_sales DESC
                                        LIMIT 3""",
                                        (branch_id,)
                          )
                      else:
                          sql_cursor.execute(
                                """SELECT b.branch_id, b.branch_name,
                                    SUM(cs.gross_sales) AS total_gross_sales
                                    FROM branches b
                                    JOIN customer_sales cs ON b.branch_id = cs.branch_id
                                    WHERE b.branch_id = %s
                                    GROUP BY b.branch_id, b.branch_name
                                    ORDER BY total_gross_sales DESC
                                    LIMIT 1""",
                                    (branch_id,)
                          )
                  rows = sql_cursor.fetchall()
                  columns = [col[0] for col in sql_cursor.description]
                  df = pd.DataFrame(rows, columns=columns)
                  st.subheader("Query Results")
                  st.dataframe(df, use_container_width=True)
                  st.success(f"Query executed successfully. Rows returned: {len(df)}")
                  sql_cursor.close()

              except Exception as e:
                  st.error(f"Query failed: {e}")



