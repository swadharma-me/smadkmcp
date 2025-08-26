import os
import sys
import logging
import contextlib
from typing import Optional, Dict, Any, List, Tuple, Union, ContextManager
import psycopg2
import psycopg2.extras
import psycopg2.pool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.config import config
from typing import Generator

# All DB parameters are always sourced from config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration class (always uses config)"""
    def __init__(self):
        self.host = config.DB_HOST
        self.port = config.DB_PORT
        self.database = config.DB_NAME
        self.user = config.DB_USER
        self.password = config.DB_PASSWORD
        self.schema = config.DB_SCHEMA
        self.min_connections = config.DB_MIN_CONNECTIONS
        self.max_connections = config.DB_MAX_CONNECTIONS
        self.connect_timeout = getattr(config, 'DB_CONNECT_TIMEOUT', 30)

        # Log all DB config values for debugging
        logger.info(f"[DB CONFIG] host={self.host} port={self.port} db={self.database} user={self.user} password={self.password} schema={self.schema} min={self.min_connections} max={self.max_connections} timeout={self.connect_timeout}")

    def get_connection_params(self) -> Dict[str, Any]:
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'connect_timeout': self.connect_timeout,
            'application_name': 'dataingestion_pipeline'
        }

    def get_connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

# Global database configuration
db_config = DatabaseConfig()

# Global connection pool
_connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

def initialize_connection_pool() -> bool:
    """Initialize the connection pool"""
    global _connection_pool
    
    try:
        if _connection_pool is None:
            logger.info(f"Initializing connection pool to {db_config.host}:{db_config.port}/{db_config.database}")
            
            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=db_config.min_connections,
                maxconn=db_config.max_connections,
                **db_config.get_connection_params()
            )
            
            logger.info(f"Connection pool initialized: {db_config.min_connections}-{db_config.max_connections} connections")
            return True
            
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        return False
    
    return True

def close_connection_pool():
    """Close the connection pool"""
    global _connection_pool
    
    if _connection_pool:
        try:
            _connection_pool.closeall()
            _connection_pool = None
            logger.info("Connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")

@contextlib.contextmanager
def get_connection(use_pool: bool = True) -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Get a database connection (context manager)
    
    Args:
        use_pool: Whether to use connection pooling
        
    Yields:
        psycopg2 connection object
    """
    connection = None
    
    try:
        if use_pool:
            # Initialize pool if not already done
            if _connection_pool is None:
                if not initialize_connection_pool():
                    raise Exception("Failed to initialize connection pool")
            
            # Get connection from pool
            connection = _connection_pool.getconn()
            
        else:
            # Create direct connection
            connection = psycopg2.connect(**db_config.get_connection_params())
        
        yield connection
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
        
    finally:
        if connection:
            if use_pool and _connection_pool:
                # Return connection to pool
                _connection_pool.putconn(connection)
            else:
                # Close direct connection
                connection.close()

from typing import Generator

@contextlib.contextmanager
def get_cursor(connection: Optional[psycopg2.extensions.connection] = None, 
               cursor_factory=None) -> Generator[psycopg2.extensions.cursor, None, None]:
    """
    Get a database cursor (context manager)
    
    Args:
        connection: Existing connection (if None, creates new one)
        cursor_factory: Cursor factory (default: RealDictCursor)
        
    Yields:
        psycopg2 cursor object
    """
    if cursor_factory is None:
        cursor_factory = psycopg2.extras.RealDictCursor
    
    if connection:
        # Use provided connection
        cursor = connection.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()
    else:
        # Create new connection
        with get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()

def execute_query(query: str, params: Optional[Union[Tuple, Dict, List]] = None, 
                 fetch: str = 'all', commit: bool = False) -> Optional[Union[List, Dict, int]]:
    """
    Execute a query and return results
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch: 'all', 'one', 'many', or 'none'
        commit: Whether to commit the transaction
        
    Returns:
        Query results or None
    """
    try:
        with get_connection() as conn:
            with get_cursor(conn) as cursor:
                cursor.execute(query, params)
                
                if commit:
                    conn.commit()
                
                if fetch == 'all':
                    return cursor.fetchall()
                elif fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'many':
                    return cursor.fetchmany()
                elif fetch == 'none':
                    return cursor.rowcount
                else:
                    return None
                    
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise

def execute_batch(queries: List[Tuple[str, Optional[Union[Tuple, Dict, List]]]], 
                 commit: bool = True) -> bool:
    """
    Execute multiple queries in a single transaction
    
    Args:
        queries: List of (query, params) tuples
        commit: Whether to commit the transaction
        
    Returns:
        Success status
    """
    try:
        with get_connection() as conn:
            with get_cursor(conn) as cursor:
                for query, params in queries:
                    cursor.execute(query, params)
                
                if commit:
                    conn.commit()
                
                return True
                
    except Exception as e:
        logger.error(f"Batch execution failed: {e}")
        return False

def test_connection() -> bool:
    """Test database connection"""
    try:
        with get_connection() as conn:
            with get_cursor(conn) as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                logger.info(f"Database connection successful: {version['version'][:50]}...")
                return True
                
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def check_extensions() -> Dict[str, bool]:
    """Check for required PostgreSQL extensions"""
    extensions = {
        'vector': False,
        'pg_trgm': False,
        'uuid-ossp': False
    }
    
    try:
        query = """
        SELECT extname 
        FROM pg_extension 
        WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp');
        """
        
        results = execute_query(query, fetch='all')
        if results:
            installed = {row['extname'] for row in results}
            for ext in extensions:
                extensions[ext] = ext in installed
        
        return extensions
        
    except Exception as e:
        logger.error(f"Failed to check extensions: {e}")
        return extensions

def check_schema_exists(schema_name: str = None) -> bool:
    """Check if schema exists"""
    if schema_name is None:
        schema_name = db_config.schema
    
    try:
        query = """
        SELECT EXISTS(
            SELECT 1 FROM information_schema.schemata 
            WHERE schema_name = %s
        );
        """
        
        result = execute_query(query, (schema_name,), fetch='one')
        return result['exists'] if result else False
        
    except Exception as e:
        logger.error(f"Failed to check schema {schema_name}: {e}")
        return False

def create_schema_if_not_exists(schema_name: str = None) -> bool:
    """Create schema if it doesn't exist"""
    if schema_name is None:
        schema_name = db_config.schema
    
    try:
        query = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
        execute_query(query, commit=True)
        logger.info(f"Schema {schema_name} created or already exists")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create schema {schema_name}: {e}")
        return False

def get_table_info(table_name: str, schema_name: str = None) -> Optional[List[Dict[str, Any]]]:
    """Get information about a table"""
    if schema_name is None:
        schema_name = db_config.schema
    
    try:
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
        """
        
        return execute_query(query, (schema_name, table_name), fetch='all')
        
    except Exception as e:
        logger.error(f"Failed to get table info for {schema_name}.{table_name}: {e}")
        return None

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    stats = {}
    
    try:
        # Database size
        size_query = """
        SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;
        """
        size_result = execute_query(size_query, fetch='one')
        stats['database_size'] = size_result['database_size'] if size_result else 'Unknown'
        
        # Connection count
        conn_query = """
        SELECT count(*) as active_connections
        FROM pg_stat_activity 
        WHERE state = 'active';
        """
        conn_result = execute_query(conn_query, fetch='one')
        stats['active_connections'] = conn_result['active_connections'] if conn_result else 0
        
        # Schema tables
        if db_config.schema:
            tables_query = """
            SELECT count(*) as table_count
            FROM information_schema.tables
            WHERE table_schema = %s;
            """
            tables_result = execute_query(tables_query, (db_config.schema,), fetch='one')
            stats['schema_tables'] = tables_result['table_count'] if tables_result else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return stats

# Convenience functions for common operations
def get_concept_nodes_count() -> int:
    """Get count of concept nodes"""
    try:
        query = f"SELECT COUNT(*) as count FROM {db_config.schema}.concept_nodes;"
        result = execute_query(query, fetch='one')
        return result['count'] if result else 0
    except Exception as e:
        logger.error(f"Failed to get concept nodes count: {e}")
        return 0

def get_embeddings_count() -> int:
    """Get count of embeddings"""
    try:
        query = f"SELECT COUNT(*) as count FROM {db_config.schema}.concept_nodes_embeddings;"
        result = execute_query(query, fetch='one')
        return result['count'] if result else 0
    except Exception as e:
        logger.error(f"Failed to get embeddings count: {e}")
        return 0

# Initialization check
def verify_setup() -> Dict[str, bool]:
    """Verify database setup"""
    checks = {
        'connection': False,
        'schema_exists': False,
        'vector_extension': False,
        'concept_nodes_table': False,
        'embeddings_table': False
    }
    
    try:
        # Test connection
        checks['connection'] = test_connection()
        
        if checks['connection']:
            # Check schema
            checks['schema_exists'] = check_schema_exists()
            
            # Check extensions
            extensions = check_extensions()
            checks['vector_extension'] = extensions.get('vector', False)
            
            # Check tables
            concept_table_info = get_table_info('concept_nodes')
            checks['concept_nodes_table'] = bool(concept_table_info)
            
            embeddings_table_info = get_table_info('concept_nodes_embeddings')
            checks['embeddings_table'] = bool(embeddings_table_info)
        
        return checks
        
    except Exception as e:
        logger.error(f"Setup verification failed: {e}")
        return checks

if __name__ == "__main__":
    """Test the database connection when run directly"""
    print("Testing PostgreSQL connection...")
    print(f"Configuration:")
    print(f"  Host: {db_config.host}")
    print(f"  Port: {db_config.port}")
    print(f"  Database: {db_config.database}")
    print(f"  User: {db_config.user}")
    print(f"  Schema: {db_config.schema}")
    print()
    
    # Run verification
    checks = verify_setup()
    
    print("Setup Verification:")
    for check, status in checks.items():
        status_str = "✓" if status else "✗"
        print(f"  {status_str} {check.replace('_', ' ').title()}")
    
    if checks['connection']:
        print("\nDatabase Statistics:")
        stats = get_database_stats()
        for stat, value in stats.items():
            print(f"  {stat.replace('_', ' ').title()}: {value}")
        
        print(f"\nConcept Nodes: {get_concept_nodes_count()}")
        print(f"Embeddings: {get_embeddings_count()}")
    
    print("\nConnection test completed!")
