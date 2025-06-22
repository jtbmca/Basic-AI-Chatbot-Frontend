# File Path Injection Security Plan

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current Vulnerability Assessment](#current-vulnerability-assessment)
3. [Attack Vectors & Risks](#attack-vectors--risks)
4. [Security Requirements](#security-requirements)
5. [Implementation Strategy](#implementation-strategy)
6. [Technical Solutions](#technical-solutions)
7. [Code Implementation Plan](#code-implementation-plan)
8. [Testing & Validation](#testing--validation)
9. [Monitoring & Detection](#monitoring--detection)
10. [Deployment Checklist](#deployment-checklist)

## Executive Summary

This document outlines a comprehensive security plan to address file path injection vulnerabilities in the local chat client application. The plan focuses on implementing industry-standard file path validation, access controls, and security monitoring to prevent unauthorized file system access.

### Key Security Objectives
- **Prevent Path Traversal**: Block attempts to access files outside allowed directories
- **Validate File Operations**: Ensure all file paths are sanitized and validated
- **Implement Access Controls**: Restrict file system access to authorized locations only
- **Enable Security Monitoring**: Track and alert on suspicious file access patterns

## Current Vulnerability Assessment

### Identified Risks in Current Codebase

1. **Direct File Path Construction**
   ```python
   # VULNERABLE: Direct path construction from user input
   file_path = os.path.join(base_dir, user_filename)
   ```

2. **Insufficient Path Validation**
   - No validation of file extension whitelist
   - No path traversal prevention
   - No canonicalization of paths

3. **Missing Access Controls**
   - No restriction on accessible directories
   - No file permission checks
   - No file size limits

4. **Configuration File Handling**
   - Hardcoded file paths in application
   - No validation of configuration file paths
   - Missing error handling for file operations

### Risk Assessment Matrix

| Vulnerability | Likelihood | Impact | Risk Level |
|---------------|------------|--------|------------|
| Path Traversal | High | High | **Critical** |
| Arbitrary File Read | Medium | High | **High** |
| Configuration Tampering | Medium | Medium | **Medium** |
| Directory Enumeration | Low | Medium | **Low** |

## Attack Vectors & Risks

### 1. Path Traversal Attacks
```bash
# Examples of malicious inputs
../../../etc/passwd
..\\..\\..\\windows\\system32\\config\\sam
....//....//....//etc/passwd
%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd
```

**Potential Impact:**
- Access to sensitive system files
- Exposure of configuration files
- Reading of other users' data
- Information disclosure

### 2. File Extension Bypass
```bash
# Attempting to access executable files
malicious.exe
script.py.txt
config.json.backup
```

**Potential Impact:**
- Execution of malicious code
- Access to backup files
- Configuration file exposure

### 3. Symbolic Link Attacks
```bash
# Creating symbolic links to sensitive files
ln -s /etc/passwd safe_file.txt
mklink safe_file.txt C:\Windows\System32\config\SAM
```

**Potential Impact:**
- Bypassing directory restrictions
- Accessing files outside allowed paths
- Privilege escalation

## Security Requirements

### 1. Functional Requirements
- **FR-1**: Validate all file paths before file operations
- **FR-2**: Restrict file access to designated safe directories
- **FR-3**: Implement file extension whitelist
- **FR-4**: Canonicalize all file paths
- **FR-5**: Log all file access attempts

### 2. Security Requirements
- **SR-1**: Prevent path traversal attacks (../../../)
- **SR-2**: Block access to system directories
- **SR-3**: Validate file permissions before access
- **SR-4**: Implement file size limits
- **SR-5**: Detect and prevent symbolic link attacks

### 3. Performance Requirements
- **PR-1**: File validation must complete within 100ms
- **PR-2**: Security checks must not impact user experience
- **PR-3**: Logging must be asynchronous

## Implementation Strategy

### Phase 1: Core Security Infrastructure (Week 1)
1. **Secure File Path Validator**
   - Path canonicalization
   - Traversal attack prevention
   - Extension validation

2. **Safe Directory Manager**
   - Define allowed directories
   - Implement access controls
   - Directory isolation

### Phase 2: Application Integration (Week 2)
1. **Refactor File Operations**
   - Replace direct file access
   - Integrate path validation
   - Add error handling

2. **Configuration Security**
   - Secure config file loading
   - Validate configuration paths
   - Environment variable validation

### Phase 3: Monitoring & Testing (Week 3)
1. **Security Monitoring**
   - File access logging
   - Anomaly detection
   - Alert system

2. **Comprehensive Testing**
   - Security test suite
   - Penetration testing
   - Performance validation

## Technical Solutions

### 1. Secure Path Validator Class
```python
import os
import pathlib
from typing import List, Optional, Tuple
import logging

class SecurePathValidator:
    """Secure file path validation and sanitization"""
    
    def __init__(self, 
                 allowed_directories: List[str],
                 allowed_extensions: List[str] = None,
                 max_path_length: int = 260,
                 case_sensitive: bool = False):
        self.allowed_directories = [
            os.path.abspath(os.path.expanduser(d)) 
            for d in allowed_directories
        ]
        self.allowed_extensions = allowed_extensions or []
        self.max_path_length = max_path_length
        self.case_sensitive = case_sensitive
        self.logger = logging.getLogger(__name__)
    
    def validate_path(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate file path for security
        Returns: (is_valid, error_message, sanitized_path)
        """
        try:
            # Basic input validation
            if not file_path or not isinstance(file_path, str):
                return False, "Invalid file path", None
            
            # Length check
            if len(file_path) > self.max_path_length:
                return False, f"Path too long (max {self.max_path_length})", None
            
            # Normalize path
            sanitized_path = self._normalize_path(file_path)
            if not sanitized_path:
                return False, "Path normalization failed", None
            
            # Path traversal check
            if not self._check_path_traversal(sanitized_path):
                return False, "Path traversal attempt detected", None
            
            # Directory restriction check
            if not self._check_directory_access(sanitized_path):
                return False, "Access to directory not allowed", None
            
            # Extension validation
            if not self._check_file_extension(sanitized_path):
                return False, "File extension not allowed", None
            
            # Symbolic link check
            if not self._check_symbolic_links(sanitized_path):
                return False, "Symbolic links not allowed", None
            
            return True, "Valid path", sanitized_path
            
        except Exception as e:
            self.logger.error(f"Path validation error: {e}")
            return False, "Path validation failed", None
    
    def _normalize_path(self, file_path: str) -> Optional[str]:
        """Normalize and canonicalize file path"""
        try:
            # Remove null bytes and control characters
            cleaned_path = ''.join(c for c in file_path if ord(c) >= 32)
            
            # Expand user directory
            expanded_path = os.path.expanduser(cleaned_path)
            
            # Get absolute path
            abs_path = os.path.abspath(expanded_path)
            
            # Resolve symbolic links and normalize
            real_path = os.path.realpath(abs_path)
            
            return real_path
            
        except (OSError, ValueError) as e:
            self.logger.warning(f"Path normalization failed: {e}")
            return None
    
    def _check_path_traversal(self, file_path: str) -> bool:
        """Check for path traversal attempts"""
        # Common path traversal patterns
        traversal_patterns = [
            '..',
            '%2e%2e',
            '%2E%2E',
            '..%2f',
            '..%5c',
            '..\\',
            '../',
            '....\\',
            '..../',
        ]
        
        path_lower = file_path.lower() if not self.case_sensitive else file_path
        
        for pattern in traversal_patterns:
            if pattern in path_lower:
                return False
        
        return True
    
    def _check_directory_access(self, file_path: str) -> bool:
        """Check if path is within allowed directories"""
        for allowed_dir in self.allowed_directories:
            try:
                # Check if file path starts with allowed directory
                if file_path.startswith(allowed_dir + os.sep) or file_path == allowed_dir:
                    return True
            except Exception:
                continue
        
        return False
    
    def _check_file_extension(self, file_path: str) -> bool:
        """Validate file extension against whitelist"""
        if not self.allowed_extensions:
            return True  # No extension restrictions
        
        _, ext = os.path.splitext(file_path)
        ext_lower = ext.lower()
        
        allowed_exts_lower = [e.lower() for e in self.allowed_extensions]
        return ext_lower in allowed_exts_lower
    
    def _check_symbolic_links(self, file_path: str) -> bool:
        """Check for symbolic links in path"""
        try:
            # Check if any part of the path is a symbolic link
            path_parts = pathlib.Path(file_path).parts
            current_path = pathlib.Path(path_parts[0])
            
            for part in path_parts[1:]:
                current_path = current_path / part
                if current_path.is_symlink():
                    return False
            
            return True
            
        except Exception:
            return False
```

### 2. Safe File Operations Manager
```python
class SafeFileManager:
    """Secure file operations with built-in validation"""
    
    def __init__(self, validator: SecurePathValidator):
        self.validator = validator
        self.logger = logging.getLogger(__name__)
    
    def safe_read_file(self, 
                      file_path: str, 
                      max_size: int = 10 * 1024 * 1024,  # 10MB default
                      encoding: str = 'utf-8') -> Tuple[bool, str, Optional[str]]:
        """Safely read file with validation"""
        try:
            # Validate path
            is_valid, error_msg, safe_path = self.validator.validate_path(file_path)
            if not is_valid:
                self.logger.warning(f"File read blocked: {error_msg} - {file_path}")
                return False, error_msg, None
            
            # Check if file exists
            if not os.path.exists(safe_path):
                return False, "File not found", None
            
            # Check file size
            file_size = os.path.getsize(safe_path)
            if file_size > max_size:
                return False, f"File too large (max {max_size} bytes)", None
            
            # Check file permissions
            if not os.access(safe_path, os.R_OK):
                return False, "File not readable", None
            
            # Read file safely
            with open(safe_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.logger.info(f"Safe file read: {safe_path}")
            return True, "File read successfully", content
            
        except PermissionError:
            return False, "Permission denied", None
        except UnicodeDecodeError:
            return False, "File encoding error", None
        except Exception as e:
            self.logger.error(f"File read error: {e}")
            return False, "File read failed", None
    
    def safe_write_file(self, 
                       file_path: str, 
                       content: str,
                       max_size: int = 10 * 1024 * 1024,
                       encoding: str = 'utf-8',
                       create_dirs: bool = False) -> Tuple[bool, str]:
        """Safely write file with validation"""
        try:
            # Validate path
            is_valid, error_msg, safe_path = self.validator.validate_path(file_path)
            if not is_valid:
                self.logger.warning(f"File write blocked: {error_msg} - {file_path}")
                return False, error_msg
            
            # Check content size
            content_size = len(content.encode(encoding))
            if content_size > max_size:
                return False, f"Content too large (max {max_size} bytes)"
            
            # Create directory if needed
            if create_dirs:
                os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            
            # Check directory write permissions
            parent_dir = os.path.dirname(safe_path)
            if not os.access(parent_dir, os.W_OK):
                return False, "Directory not writable"
            
            # Write file safely with atomic operation
            temp_path = safe_path + '.tmp'
            try:
                with open(temp_path, 'w', encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic move
                if os.name == 'nt':  # Windows
                    if os.path.exists(safe_path):
                        os.remove(safe_path)
                os.rename(temp_path, safe_path)
                
                self.logger.info(f"Safe file write: {safe_path}")
                return True, "File written successfully"
                
            finally:
                # Clean up temp file if it exists
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
            
        except PermissionError:
            return False, "Permission denied"
        except OSError as e:
            return False, f"File system error: {e}"
        except Exception as e:
            self.logger.error(f"File write error: {e}")
            return False, "File write failed"
    
    def safe_list_directory(self, dir_path: str) -> Tuple[bool, str, Optional[List[str]]]:
        """Safely list directory contents"""
        try:
            # Validate directory path
            is_valid, error_msg, safe_path = self.validator.validate_path(dir_path)
            if not is_valid:
                self.logger.warning(f"Directory list blocked: {error_msg} - {dir_path}")
                return False, error_msg, None
            
            # Check if directory exists
            if not os.path.exists(safe_path):
                return False, "Directory not found", None
            
            if not os.path.isdir(safe_path):
                return False, "Path is not a directory", None
            
            # Check directory permissions
            if not os.access(safe_path, os.R_OK):
                return False, "Directory not readable", None
            
            # List directory contents
            contents = []
            for item in os.listdir(safe_path):
                item_path = os.path.join(safe_path, item)
                # Only include files that pass validation
                is_valid_item, _, _ = self.validator.validate_path(item_path)
                if is_valid_item:
                    contents.append(item)
            
            self.logger.info(f"Safe directory list: {safe_path}")
            return True, "Directory listed successfully", contents
            
        except PermissionError:
            return False, "Permission denied", None
        except Exception as e:
            self.logger.error(f"Directory list error: {e}")
            return False, "Directory list failed", None
```

### 3. Configuration Security Manager
```python
class SecureConfigManager:
    """Secure configuration file management"""
    
    def __init__(self, 
                 config_directory: str,
                 allowed_config_files: List[str]):
        self.config_directory = os.path.abspath(config_directory)
        self.allowed_config_files = allowed_config_files
        
        # Set up secure path validator for config files
        self.validator = SecurePathValidator(
            allowed_directories=[self.config_directory],
            allowed_extensions=['.json', '.yaml', '.yml', '.env', '.ini'],
            max_path_length=260
        )
        
        self.file_manager = SafeFileManager(self.validator)
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_name: str) -> dict:
        """Securely load configuration file"""
        if config_name not in self.allowed_config_files:
            raise ValueError(f"Configuration file not allowed: {config_name}")
        
        config_path = os.path.join(self.config_directory, config_name)
        
        success, message, content = self.file_manager.safe_read_file(config_path)
        if not success:
            raise FileNotFoundError(f"Failed to load config: {message}")
        
        # Parse based on file extension
        _, ext = os.path.splitext(config_name)
        
        try:
            if ext.lower() == '.json':
                import json
                return json.loads(content)
            elif ext.lower() in ['.yaml', '.yml']:
                import yaml
                return yaml.safe_load(content)
            elif ext.lower() == '.env':
                return self._parse_env_file(content)
            else:
                raise ValueError(f"Unsupported config format: {ext}")
                
        except Exception as e:
            raise ValueError(f"Failed to parse config file: {e}")
    
    def save_config(self, config_name: str, config_data: dict) -> bool:
        """Securely save configuration file"""
        if config_name not in self.allowed_config_files:
            raise ValueError(f"Configuration file not allowed: {config_name}")
        
        config_path = os.path.join(self.config_directory, config_name)
        
        # Serialize based on file extension
        _, ext = os.path.splitext(config_name)
        
        try:
            if ext.lower() == '.json':
                import json
                content = json.dumps(config_data, indent=2)
            elif ext.lower() in ['.yaml', '.yml']:
                import yaml
                content = yaml.dump(config_data, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported config format for writing: {ext}")
            
            success, message = self.file_manager.safe_write_file(
                config_path, content, create_dirs=True
            )
            
            if not success:
                raise IOError(f"Failed to save config: {message}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Config save error: {e}")
            raise
    
    def _parse_env_file(self, content: str) -> dict:
        """Parse .env file format"""
        config = {}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
        return config
```

## Code Implementation Plan

### 1. Integration with Current Application

**Step 1: Update app.py imports and initialization**
```python
# Add to app.py imports
from secure_file_manager import SecurePathValidator, SafeFileManager, SecureConfigManager

# Initialize secure file handling
def initialize_security():
    """Initialize secure file handling"""
    
    # Define allowed directories
    allowed_dirs = [
        os.path.join(os.getcwd(), 'conversations'),
        os.path.join(os.getcwd(), 'data'),
        os.path.join(os.getcwd(), 'models'),
        os.path.join(os.getcwd(), 'config')
    ]
    
    # Create directories if they don't exist
    for directory in allowed_dirs:
        os.makedirs(directory, exist_ok=True)
    
    # Set up path validator
    validator = SecurePathValidator(
        allowed_directories=allowed_dirs,
        allowed_extensions=['.json', '.txt', '.pkl', '.pt', '.env'],
        max_path_length=260
    )
    
    # Set up file manager
    file_manager = SafeFileManager(validator)
    
    # Set up config manager
    config_manager = SecureConfigManager(
        config_directory='config',
        allowed_config_files=['config.json', 'personas.json', '.env']
    )
    
    return validator, file_manager, config_manager
```

**Step 2: Replace file operations**
```python
# Replace existing file operations with secure versions
def load_chat_history_secure(file_manager: SafeFileManager):
    """Securely load chat history"""
    success, message, content = file_manager.safe_read_file('chat_history.json')
    if success:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            st.error("Chat history file is corrupted")
            return []
    else:
        if "File not found" in message:
            return []  # New installation
        else:
            st.error(f"Failed to load chat history: {message}")
            return []

def save_chat_history_secure(file_manager: SafeFileManager, history: list):
    """Securely save chat history"""
    try:
        content = json.dumps(history, indent=2)
        success, message = file_manager.safe_write_file('chat_history.json', content)
        if not success:
            st.error(f"Failed to save chat history: {message}")
    except Exception as e:
        st.error(f"Error saving chat history: {e}")
```

### 2. Environment Configuration Updates

**Updated .env.example**
```env
# Security Configuration
SECURE_MODE=true
MAX_FILE_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=.json,.txt,.pkl,.pt,.env
LOG_FILE_ACCESS=true

# Existing configuration...
BERT_MODEL_PATH=models/bert-base-uncased
CONVERSATIONS_DIR=conversations
PERSONAS_FILE=custom_personas.json
CHAT_HISTORY_FILE=chat_history.json
```

### 3. Error Handling and User Feedback

```python
def handle_file_security_error(error_message: str):
    """Handle file security errors with user-friendly messages"""
    
    error_mappings = {
        "Path traversal attempt detected": "Invalid file path. Please use a valid filename.",
        "Access to directory not allowed": "File location not permitted.",
        "File extension not allowed": "File type not supported.",
        "File too large": "File size exceeds the limit.",
        "Permission denied": "Insufficient permissions to access the file."
    }
    
    user_message = error_mappings.get(error_message, "File operation failed for security reasons.")
    
    st.error(user_message)
    st.info("Please contact support if this error persists.")
```

## Testing & Validation

### 1. Security Test Suite
```python
import pytest
import tempfile
import os

class TestSecurePathValidator:
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = SecurePathValidator(
            allowed_directories=[self.temp_dir],
            allowed_extensions=['.txt', '.json'],
            max_path_length=100
        )
    
    def test_path_traversal_attacks(self):
        """Test protection against path traversal"""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
        ]
        
        for path in malicious_paths:
            is_valid, error, _ = self.validator.validate_path(path)
            assert not is_valid, f"Should block path traversal: {path}"
            assert "traversal" in error.lower()
    
    def test_extension_validation(self):
        """Test file extension validation"""
        valid_path = os.path.join(self.temp_dir, 'test.txt')
        invalid_path = os.path.join(self.temp_dir, 'test.exe')
        
        is_valid, _, _ = self.validator.validate_path(valid_path)
        assert is_valid, "Should allow .txt files"
        
        is_valid, error, _ = self.validator.validate_path(invalid_path)
        assert not is_valid, "Should block .exe files"
        assert "extension" in error.lower()
    
    def test_directory_restriction(self):
        """Test directory access restrictions"""
        allowed_path = os.path.join(self.temp_dir, 'allowed.txt')
        forbidden_path = '/etc/passwd'
        
        is_valid, _, _ = self.validator.validate_path(allowed_path)
        assert is_valid, "Should allow access to permitted directory"
        
        is_valid, error, _ = self.validator.validate_path(forbidden_path)
        assert not is_valid, "Should block access to forbidden directory"
        assert "directory" in error.lower()
    
    def test_symbolic_link_detection(self):
        """Test symbolic link detection"""
        # Create a symbolic link (Unix/Linux only)
        if os.name != 'nt':
            target_file = os.path.join(self.temp_dir, 'target.txt')
            link_file = os.path.join(self.temp_dir, 'link.txt')
            
            with open(target_file, 'w') as f:
                f.write('test')
            
            os.symlink(target_file, link_file)
            
            is_valid, error, _ = self.validator.validate_path(link_file)
            assert not is_valid, "Should block symbolic links"
```

### 2. Penetration Testing Checklist

**Manual Security Tests:**
- [ ] Path traversal with various encodings
- [ ] Null byte injection
- [ ] Long path names (buffer overflow)
- [ ] Unicode normalization attacks
- [ ] Case sensitivity bypass attempts
- [ ] Symbolic link creation and access
- [ ] Directory permission escalation
- [ ] File size limit bypass
- [ ] Extension spoofing

**Automated Security Tests:**
- [ ] SAST (Static Application Security Testing)
- [ ] Dependency vulnerability scanning
- [ ] Fuzzing file path inputs
- [ ] Configuration security audit

## Monitoring & Detection

### 1. Security Event Logging
```python
import logging
from datetime import datetime
import json

class SecurityLogger:
    """Security-focused logging for file operations"""
    
    def __init__(self, log_file: str = 'security.log'):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # File handler for security logs
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_file_access(self, 
                       operation: str, 
                       file_path: str, 
                       success: bool,
                       error_message: str = None,
                       user_id: str = None):
        """Log file access attempts"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'file_path': file_path,
            'success': success,
            'user_id': user_id or 'unknown',
            'error_message': error_message
        }
        
        if success:
            self.logger.info(f"FILE_ACCESS: {json.dumps(log_data)}")
        else:
            self.logger.warning(f"FILE_ACCESS_BLOCKED: {json.dumps(log_data)}")
    
    def log_security_violation(self, 
                             violation_type: str, 
                             details: dict):
        """Log security violations"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'violation_type': violation_type,
            'details': details
        }
        
        self.logger.error(f"SECURITY_VIOLATION: {json.dumps(log_data)}")
```

### 2. Anomaly Detection
```python
from collections import defaultdict, deque
from datetime import datetime, timedelta

class FileAccessAnomalyDetector:
    """Detect anomalous file access patterns"""
    
    def __init__(self, 
                 time_window: int = 300,  # 5 minutes
                 max_attempts: int = 50):
        self.time_window = time_window
        self.max_attempts = max_attempts
        self.access_history = defaultdict(deque)
        self.blocked_attempts = defaultdict(int)
    
    def check_access_pattern(self, user_id: str, file_path: str) -> bool:
        """Check if access pattern is anomalous"""
        now = datetime.now()
        
        # Clean old entries
        self._clean_old_entries(user_id, now)
        
        # Add current access
        self.access_history[user_id].append(now)
        
        # Check for anomalous patterns
        if len(self.access_history[user_id]) > self.max_attempts:
            return True  # Too many attempts
        
        return False
    
    def record_blocked_attempt(self, user_id: str, violation_type: str):
        """Record blocked access attempt"""
        self.blocked_attempts[f"{user_id}:{violation_type}"] += 1
    
    def _clean_old_entries(self, user_id: str, current_time: datetime):
        """Remove entries outside time window"""
        cutoff_time = current_time - timedelta(seconds=self.time_window)
        
        while (self.access_history[user_id] and 
               self.access_history[user_id][0] < cutoff_time):
            self.access_history[user_id].popleft()
```

## Deployment Checklist

### Pre-Deployment Security Checks
- [ ] **Code Review**: Security-focused code review completed
- [ ] **Static Analysis**: SAST scan passed with no high-risk findings
- [ ] **Dependency Scan**: All dependencies scanned for vulnerabilities
- [ ] **Configuration Audit**: All configuration files reviewed
- [ ] **Permission Review**: File system permissions properly configured
- [ ] **Test Coverage**: Security tests achieve >90% coverage
- [ ] **Documentation**: Security documentation updated

### Deployment Steps
1. **Backup Current System**
   ```bash
   # Create backup of current application
   cp -r /current/app /backup/app_$(date +%Y%m%d_%H%M%S)
   ```

2. **Deploy Security Components**
   ```bash
   # Deploy new security modules
   pip install -r requirements.txt
   python -m pytest tests/security/
   ```

3. **Configuration Migration**
   ```bash
   # Migrate configuration files
   python migrate_config.py --verify-security
   ```

4. **Validation Testing**
   ```bash
   # Run security validation tests
   python -m pytest tests/security/test_file_security.py -v
   ```

### Post-Deployment Monitoring
- [ ] **Log Monitoring**: Security logs are being generated
- [ ] **Anomaly Detection**: Anomaly detection system is active
- [ ] **Performance Impact**: No significant performance degradation
- [ ] **User Experience**: No negative impact on user workflows
- [ ] **Error Rates**: No increase in application errors

### Rollback Plan
If security implementation causes issues:

1. **Immediate Rollback**
   ```bash
   # Quick rollback to previous version
   git checkout HEAD~1
   systemctl restart app
   ```

2. **Gradual Rollback**
   - Disable security features via configuration
   - Monitor for stability
   - Plan fixes for next deployment

### Success Metrics
- **Security**: Zero successful path traversal attacks
- **Performance**: File operations complete within 200ms
- **Reliability**: 99.9% uptime maintained
- **User Experience**: No user complaints about file access issues

## Conclusion

This comprehensive file path injection security plan provides:

1. **Immediate Protection**: Blocks common attack vectors
2. **Defense in Depth**: Multiple layers of security
3. **Monitoring**: Comprehensive logging and anomaly detection
4. **Maintainability**: Clean, well-documented code
5. **Performance**: Minimal impact on application performance

The implementation should be done in phases with thorough testing at each stage to ensure both security and functionality are maintained.
