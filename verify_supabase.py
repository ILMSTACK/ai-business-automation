# verify_supabase.py
"""
Supabase Database Connection Verification Tool
Validates database connectivity and environment configuration for Flask application.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()


class DatabaseConnectionVerifier:
    """
    Database connection verification utility for Supabase PostgreSQL integration.
    """

    def __init__(self):
        self.database_url = os.getenv('SUPABASE_DATABASE_URL')
        self.connection_successful = False
        self.error_details = None

    def print_header(self):
        """Print application header information."""
        print("=" * 80)
        print("SUPABASE DATABASE CONNECTION VERIFICATION")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        print("-" * 80)

    def check_environment_variables(self):
        """Validate required environment variables are present."""
        print("STEP 1: Environment Variable Validation")
        print("-" * 40)

        if not self.database_url:
            print("STATUS: FAILED")
            print("ERROR: SUPABASE_DATABASE_URL environment variable not found")
            print("SOLUTION: Ensure .env file contains valid database connection string")
            return False

        # Mask password for security in logs
        masked_url = self._mask_password(self.database_url)
        print("STATUS: SUCCESS")
        print(f"DATABASE_URL: {masked_url}")
        return True

    def test_database_connection(self):
        """Establish and test database connection."""
        print("\nSTEP 2: Database Connection Test")
        print("-" * 40)

        try:
            # Configure connection with production-ready settings
            engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False
            )

            print("STATUS: Attempting connection...")

            with engine.connect() as connection:
                # Test basic connectivity
                result = connection.execute(text("SELECT version()"))
                version_info = result.fetchone()[0]

                # Verify database details
                db_result = connection.execute(text("SELECT current_database()"))
                database_name = db_result.fetchone()[0]

                user_result = connection.execute(text("SELECT current_user"))
                current_user = user_result.fetchone()[0]

                # Check schema and tables
                tables_result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))

                existing_tables = [row[0] for row in tables_result.fetchall()]

                self.connection_successful = True

                print("STATUS: SUCCESS")
                print(f"PostgreSQL Version: {version_info[:100]}")
                print(f"Database Name: {database_name}")
                print(f"Connected User: {current_user}")
                print(f"Existing Tables: {len(existing_tables)} found")

                if existing_tables:
                    print("Tables:")
                    for table in existing_tables:
                        print(f"  - {table}")
                else:
                    print("Note: No user tables found - this is normal for new installations")

                return True

        except Exception as e:
            self.error_details = str(e)
            print("STATUS: FAILED")
            print(f"ERROR: {self.error_details}")
            return False

    def analyze_connection_error(self):
        """Provide detailed error analysis and recommendations."""
        if not self.error_details:
            return

        print("\nSTEP 3: Error Analysis and Recommendations")
        print("-" * 40)

        error_lower = self.error_details.lower()

        if "password authentication failed" in error_lower:
            print("ERROR TYPE: Authentication Failure")
            print("CAUSE: Invalid database credentials")
            print("SOLUTIONS:")
            print("  1. Verify password in Supabase Dashboard > Settings > Database")
            print("  2. Reset database password if necessary")
            print("  3. Ensure connection string format: postgresql://user:password@host:port/db")
            print("  4. Remove any brackets or special formatting from password")

        elif "connection refused" in error_lower or "timeout" in error_lower:
            print("ERROR TYPE: Network Connectivity Issue")
            print("CAUSE: Cannot reach database server")
            print("SOLUTIONS:")
            print("  1. Verify Supabase project is active (not paused)")
            print("  2. Check internet connectivity")
            print("  3. Verify firewall settings allow PostgreSQL connections")
            print("  4. Try different connection mode (Direct vs Pooled)")

        elif "invalid dsn" in error_lower or "invalid connection" in error_lower:
            print("ERROR TYPE: Connection String Format Error")
            print("CAUSE: Malformed database URL")
            print("SOLUTIONS:")
            print("  1. Get fresh connection string from Supabase Dashboard")
            print("  2. Remove any query parameters (?pgbouncer=true)")
            print("  3. Ensure proper URL encoding of special characters")

        else:
            print("ERROR TYPE: Unknown Connection Issue")
            print("CAUSE: Unidentified database connection problem")
            print("SOLUTIONS:")
            print("  1. Check Supabase service status")
            print("  2. Verify database configuration")
            print("  3. Contact Supabase support if issue persists")

    def generate_summary_report(self):
        """Generate final verification summary."""
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)

        if self.connection_successful:
            print("OVERALL STATUS: SUCCESS")
            print("DATABASE: Ready for application deployment")
            print("NEXT STEPS:")
            print("  1. Run database migrations: python create_tables.py")
            print("  2. Start Flask application: python app.py")
            print("  3. Test API endpoints")
        else:
            print("OVERALL STATUS: FAILED")
            print("DATABASE: Configuration requires attention")
            print("NEXT STEPS:")
            print("  1. Address connection issues identified above")
            print("  2. Re-run verification after fixes")
            print("  3. Contact system administrator if needed")

        print("=" * 80)

    def _mask_password(self, url):
        """Mask password in connection string for secure logging."""
        if ':' in url and '@' in url:
            try:
                # Extract password portion and mask it
                parts = url.split('://')
                if len(parts) == 2:
                    protocol, remainder = parts
                    if '@' in remainder:
                        credentials, host_part = remainder.split('@', 1)
                        if ':' in credentials:
                            username, password = credentials.split(':', 1)
                            masked_password = '*' * min(len(password), 8)
                            return f"{protocol}://{username}:{masked_password}@{host_part}"
            except:
                pass
        return url[:50] + "..." if len(url) > 50 else url


def main():
    """Main verification workflow."""
    verifier = DatabaseConnectionVerifier()

    # Execute verification steps
    verifier.print_header()

    env_check = verifier.check_environment_variables()
    if not env_check:
        verifier.generate_summary_report()
        sys.exit(1)

    connection_check = verifier.test_database_connection()
    if not connection_check:
        verifier.analyze_connection_error()

    verifier.generate_summary_report()

    # Exit with appropriate code
    sys.exit(0 if verifier.connection_successful else 1)


if __name__ == "__main__":
    main()