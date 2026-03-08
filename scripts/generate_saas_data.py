"""
Synthetic SaaS Data Generator

This script generates synthetic SaaS subscription data including:

- customers
- subscriptions
- invoices
- payments
- churn events
- plan changes

The generated data is inserted into a PostgreSQL database and used
for analytics projects including SQL analysis, Power BI dashboards,
and Kaggle datasets.
"""





import psycopg2
import random
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

PAYMENT_FAILURE_RATE = 0.07
SIMULATION_END = date(2025, 12, 31)


MONTHLY_CHURN = {
    "Free": 0.06,
    "Basic": 0.05,
    "Pro": 0.03,
    "Premium": 0.02
}

CHURN_REASONS = ["price", "product_fit", "competitor", "budget", "other"]



db_config = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}
SIMULATION_START = date(2023, 1, 1)
SIMULATION_END = date(2025, 12, 31)

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def generate_customers(cur):
    print("Generating customers...")

    customers_data = []

    for year, count in {2023: 5000, 2024: 8000, 2025: 12000}.items():
        start = date(year, 1, 1)
        end = date(year, 12, 31)

        for _ in range(count):
            signup_date = random_date(start, end)
            company_size = random.choice(["small", "medium", "large"])
            industry = random.choice(["tech", "finance", "retail", "health"])
            acquisition_channel = random.choice(["organic", "ads", "referral"])
            country = random.choice(["Germany", "US", "UK", "India"])

            customers_data.append(
                (signup_date, company_size, industry, acquisition_channel, country)
            )

    cur.executemany("""
        INSERT INTO customers 
        (signup_date, company_size, industry, acquisition_channel, country)
        VALUES (%s, %s, %s, %s, %s)
    """, customers_data)

    print(f"Inserted {len(customers_data)} customers.")

def generate_subscriptions(cur):
    print("Generating subscriptions...")

    cur.execute("SELECT customer_id, signup_date FROM customers;")
    customers = cur.fetchall()

    subscriptions_data = []

    for customer_id, signup_date in customers:

        r = random.random()

        if r < 0.60:
            plan_name = "Free"
            billing_interval = "monthly"
        elif r < 0.85:
            plan_name = "Basic"
            billing_interval = "annual" if random.random() < 0.35 else "monthly"
        elif r < 0.95:
            plan_name = "Pro"
            billing_interval = "annual" if random.random() < 0.35 else "monthly"
        else:
            plan_name = "Premium"
            billing_interval = "annual" if random.random() < 0.35 else "monthly"

        cur.execute("""
            SELECT plan_id 
            FROM subscription_plans 
            WHERE plan_name = %s AND billing_interval = %s
        """, (plan_name, billing_interval))

        plan_id = cur.fetchone()[0]

        subscriptions_data.append(
            (customer_id, signup_date, None, "active", plan_id)
        )

    cur.executemany("""
        INSERT INTO subscriptions
        (customer_id, subscription_start, subscription_end, status, plan_id)
        VALUES (%s, %s, %s, %s, %s)
    """, subscriptions_data)

    print(f"Inserted {len(subscriptions_data)} subscriptions.")




def generate_billing(cur):
    print("Generating invoices, payments, and churn...")

    cur.execute("""
        SELECT s.subscription_id, s.subscription_start,
               p.plan_name, p.billing_interval, p.price
        FROM subscriptions s
        JOIN subscription_plans p ON s.plan_id = p.plan_id
    """)

    subscriptions = cur.fetchall()

    invoices_data = []
    payments_data = []
    churn_data = []
    subscription_updates = []
    plan_change_data = []
    subscription_plan_updates = []

    for sub_id, start_date, plan_name, interval, price in subscriptions:

        # -------------------------
        # FREE USERS
        # -------------------------
        if plan_name == "Free":

            current_date = start_date

            while current_date <= SIMULATION_END:

                period_end = current_date + relativedelta(months=1)

                if period_end > SIMULATION_END:
                    break

                monthly_conversion_rate = 0.08 / 12

                # Conversion
                if random.random() < monthly_conversion_rate:

                    cur.execute("""
                        SELECT plan_id FROM subscription_plans
                        WHERE plan_name = 'Free' AND billing_interval = 'monthly'
                    """)
                    old_plan_id = cur.fetchone()[0]

                    cur.execute("""
                        SELECT plan_id FROM subscription_plans
                        WHERE plan_name = 'Basic' AND billing_interval = 'monthly'
                    """)
                    new_plan_id = cur.fetchone()[0]

                    plan_change_data.append(
                        (sub_id, old_plan_id, new_plan_id, period_end)
                    )

                    subscription_plan_updates.append(
                        (new_plan_id, sub_id)
                    )

                    break

                # Free churn
                if random.random() < MONTHLY_CHURN["Free"]:

                    churn_reason = random.choice(CHURN_REASONS)

                    churn_data.append(
                        (sub_id, period_end, churn_reason)
                    )

                    subscription_updates.append(
                        (period_end, "churned", sub_id)
                    )

                    break

                current_date = period_end

            continue

        # -------------------------
        # PAID USERS
        # -------------------------

        current_date = start_date
        churned = False

        if interval == "monthly":
            total_cycles = (
                (SIMULATION_END.year - start_date.year) * 12 +
                (SIMULATION_END.month - start_date.month)
            )
        else:
            total_cycles = SIMULATION_END.year - start_date.year

        for _ in range(total_cycles):

            if interval == "monthly":
                period_end = current_date + relativedelta(months=1)
                invoice_amount = price
            else:
                period_end = current_date + relativedelta(years=1)
                invoice_amount = price

            if period_end > SIMULATION_END:
                break

            invoices_data.append(
                (sub_id, current_date, period_end, invoice_amount, "paid")
            )

            payment_status = "successful"
            if random.random() < PAYMENT_FAILURE_RATE:
                payment_status = "failed"

            payments_data.append(
                (sub_id, current_date, invoice_amount, payment_status)
            )

            if payment_status == "successful":
                churn_probability = MONTHLY_CHURN[plan_name]

                if random.random() < churn_probability:
                    churn_reason = random.choice(CHURN_REASONS)

                    churn_data.append(
                        (sub_id, period_end, churn_reason)
                    )

                    subscription_updates.append(
                        (period_end, "churned", sub_id)
                    )

                    churned = True

            if churned:
                break

            current_date = period_end

    # -------------------------
    # BULK INSERTS
    # -------------------------

    cur.executemany("""
        INSERT INTO invoices
        (subscription_id, billing_period_start, billing_period_end, invoice_amount, invoice_status)
        VALUES (%s, %s, %s, %s, %s)
    """, invoices_data)

    cur.executemany("""
        INSERT INTO payments
        (subscription_id, payment_date, amount, payment_status)
        VALUES (%s, %s, %s, %s)
    """, payments_data)

    cur.executemany("""
        INSERT INTO churn_events
        (subscription_id, churn_date, churn_reason)
        VALUES (%s, %s, %s)
    """, churn_data)

    cur.executemany("""
        UPDATE subscriptions
        SET subscription_end = %s,
            status = %s
        WHERE subscription_id = %s
    """, subscription_updates)

    cur.executemany("""
        INSERT INTO plan_changes
        (subscription_id, old_plan_id, new_plan_id, change_date)
        VALUES (%s, %s, %s, %s)
    """, plan_change_data)

    cur.executemany("""
        UPDATE subscriptions
        SET plan_id = %s
        WHERE subscription_id = %s
    """, subscription_plan_updates)

    print(f"Inserted {len(invoices_data)} invoices.")
    print(f"Inserted {len(payments_data)} payments.")
    print(f"Inserted {len(churn_data)} churn events.")


def main():
    print("Starting SaaS data generation...")
    conn = get_connection()
    cur = conn.cursor()

    print("Clearing existing data...")

    cur.execute("TRUNCATE churn_events RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE plan_changes RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE payments RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE invoices RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE subscriptions RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE customers RESTART IDENTITY CASCADE;")

    conn.commit()
    print("Database reset complete.")
    generate_customers(cur)
    conn.commit()

    generate_subscriptions(cur)
    conn.commit()

    generate_billing(cur)
    conn.commit()

    cur.close()
    conn.close()
    print("Generation complete.")
if __name__ == "__main__":
    main()