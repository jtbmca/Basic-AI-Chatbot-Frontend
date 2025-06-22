# Industry Standard Rate Limiting Solutions

## Overview
Rate limiting is a critical security mechanism that controls the frequency of requests a user can make to prevent abuse, ensure fair resource allocation, and protect against denial-of-service attacks.

## 1. **Token Bucket Algorithm**

### Concept
Each user has a "bucket" with a fixed capacity of tokens. Tokens are added at a constant rate, and each request consumes one token. When the bucket is empty, requests are rejected.

### Implementation Patterns
```python
import time
from collections import defaultdict

class TokenBucket:
    def __init__(self, capacity=10, refill_rate=1):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
    
    def allow_request(self):
        now = time.time()
        # Add tokens based on time elapsed
        tokens_to_add = (now - self.last_refill) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

### Industry Tools
- **Redis + Lua Scripts**: Atomic operations for distributed systems
- **AWS API Gateway**: Built-in rate limiting with burst and sustained rates
- **Kong**: API gateway with sophisticated rate limiting plugins
- **Nginx rate limiting**: `limit_req` module for HTTP requests

## 2. **Sliding Window Algorithm**

### Concept
Tracks requests within a moving time window. More accurate than fixed windows but requires more memory.

### Implementation
```python
import time
from collections import deque

class SlidingWindowRateLimit:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    def allow_request(self):
        now = time.time()
        # Remove old requests outside the window
        while self.requests and self.requests[0] <= now - self.window_seconds:
            self.requests.popleft()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

### Industry Solutions
- **Redis Sliding Window**: Using sorted sets with timestamps
- **Elasticsearch**: Time-based aggregations for rate limiting
- **InfluxDB**: Time-series database for precise window tracking

## 3. **Fixed Window Counter**

### Concept
Simple approach that resets counters at fixed intervals (e.g., every minute).

### Implementation
```python
import time
from collections import defaultdict

class FixedWindowRateLimit:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.windows = defaultdict(int)
    
    def allow_request(self, user_id):
        current_window = int(time.time() // self.window_seconds)
        key = f"{user_id}:{current_window}"
        
        if self.windows[key] < self.max_requests:
            self.windows[key] += 1
            return True
        return False
```

## 4. **Leaky Bucket Algorithm**

### Concept
Requests are processed at a constant rate regardless of input rate. Excess requests overflow and are dropped.

### Use Cases
- Smoothing bursty traffic
- API gateways with downstream rate limits
- Message queue processing

## 5. **Industry-Standard Libraries & Tools**

### Python Libraries
```python
# Flask-Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# slowapi (FastAPI)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/")
@limiter.limit("5/minute")
async def homepage(request: Request):
    return {"message": "Hello World"}
```

### Redis-Based Solutions
```python
import redis
import time

class RedisRateLimit:
    def __init__(self, redis_client, prefix="rate_limit"):
        self.redis = redis_client
        self.prefix = prefix
    
    def is_allowed(self, identifier, limit, window_seconds):
        pipe = self.redis.pipeline()
        key = f"{self.prefix}:{identifier}"
        
        # Sliding window log approach
        now = time.time()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        
        results = pipe.execute()
        current_requests = results[1]
        
        return current_requests < limit
```

## 6. **Distributed Rate Limiting**

### Challenges
- **Coordination**: Multiple servers need to share state
- **Consistency**: Avoiding race conditions
- **Performance**: Low latency requirements

### Solutions

#### Redis Cluster
```lua
-- Lua script for atomic rate limiting
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])

-- Clean old entries
redis.call('zremrangebyscore', key, 0, current_time - window)

-- Count current requests
local current_requests = redis.call('zcard', key)

if current_requests < limit then
    -- Add current request
    redis.call('zadd', key, current_time, current_time)
    redis.call('expire', key, window)
    return {1, limit - current_requests - 1}
else
    return {0, 0}
end
```

#### Database-Based
```sql
-- PostgreSQL with advisory locks
SELECT pg_advisory_lock(hashtext('user:' || user_id));

UPDATE rate_limits 
SET request_count = CASE 
    WHEN last_reset < NOW() - INTERVAL '1 hour' THEN 1
    ELSE request_count + 1
END,
last_reset = CASE 
    WHEN last_reset < NOW() - INTERVAL '1 hour' THEN NOW()
    ELSE last_reset
END
WHERE user_id = $1;

SELECT pg_advisory_unlock(hashtext('user:' || user_id));
```

## 7. **Advanced Rate Limiting Strategies**

### Hierarchical Rate Limits
```python
class HierarchicalRateLimit:
    def __init__(self):
        self.limits = {
            'global': (1000, 3600),      # 1000 requests per hour globally
            'per_user': (100, 3600),     # 100 requests per hour per user
            'per_ip': (200, 3600),       # 200 requests per hour per IP
            'per_endpoint': (50, 300)    # 50 requests per 5 minutes per endpoint
        }
        self.limiters = {key: TokenBucket(*params) for key, params in self.limits.items()}
    
    def check_all_limits(self, user_id, ip_address, endpoint):
        checks = [
            ('global', 'global'),
            ('per_user', user_id),
            ('per_ip', ip_address),
            ('per_endpoint', endpoint)
        ]
        
        for limit_type, identifier in checks:
            if not self.limiters[limit_type].allow_request():
                return False, limit_type
        
        return True, None
```

### Adaptive Rate Limiting
```python
class AdaptiveRateLimit:
    def __init__(self, base_limit=100):
        self.base_limit = base_limit
        self.current_limit = base_limit
        self.error_rate = 0
        self.response_time = 0
    
    def adjust_limit(self, success, response_time):
        # Increase limit if system is healthy
        if success and response_time < 0.1 and self.error_rate < 0.01:
            self.current_limit = min(self.current_limit * 1.1, self.base_limit * 2)
        
        # Decrease limit if system is stressed
        elif not success or response_time > 0.5 or self.error_rate > 0.05:
            self.current_limit = max(self.current_limit * 0.9, self.base_limit * 0.5)
```

## 8. **Implementation Best Practices**

### 1. **Graceful Degradation**
```python
class GracefulRateLimit:
    def __init__(self, primary_limiter, fallback_limiter):
        self.primary = primary_limiter
        self.fallback = fallback_limiter
    
    def check_limit(self, identifier):
        try:
            return self.primary.is_allowed(identifier)
        except Exception:
            # Fall back to local rate limiting if distributed system fails
            return self.fallback.is_allowed(identifier)
```

### 2. **Rate Limit Headers**
```python
def add_rate_limit_headers(response, remaining, limit, reset_time):
    response.headers['X-RateLimit-Limit'] = str(limit)
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['X-RateLimit-Reset'] = str(reset_time)
    response.headers['Retry-After'] = str(max(0, reset_time - time.time()))
```

### 3. **Whitelisting Critical Users**
```python
class WhitelistRateLimit:
    def __init__(self, base_limiter, whitelist=None):
        self.base_limiter = base_limiter
        self.whitelist = whitelist or set()
    
    def is_allowed(self, identifier):
        if identifier in self.whitelist:
            return True
        return self.base_limiter.is_allowed(identifier)
```

## 9. **Monitoring & Alerting**

### Key Metrics
- **Rate limit hit rate**: Percentage of requests being rate limited
- **False positive rate**: Legitimate requests being blocked
- **System load correlation**: Rate limits vs. system performance
- **User behavior patterns**: Normal vs. suspicious usage

### Implementation
```python
import logging
from prometheus_client import Counter, Histogram

rate_limit_counter = Counter('rate_limit_total', 'Rate limit decisions', ['result', 'limit_type'])
request_duration = Histogram('request_duration_seconds', 'Request duration')

class MonitoredRateLimit:
    def check_limit(self, identifier, limit_type='default'):
        allowed = self.base_limiter.is_allowed(identifier)
        
        rate_limit_counter.labels(
            result='allowed' if allowed else 'blocked',
            limit_type=limit_type
        ).inc()
        
        if not allowed:
            logging.warning(f"Rate limit exceeded for {identifier} on {limit_type}")
        
        return allowed
```

## 10. **Cloud Provider Solutions**

### AWS
- **API Gateway**: Throttling settings with burst and sustained rates
- **CloudFront**: Geographic and IP-based rate limiting
- **WAF**: Complex rate limiting rules with conditions

### Google Cloud
- **Cloud Armor**: DDoS protection with rate limiting
- **API Gateway**: Quota and rate limiting policies
- **Cloud Load Balancer**: Rate limiting at the edge

### Azure
- **API Management**: Rate limiting policies
- **Front Door**: Rate limiting rules
- **Application Gateway**: Request rate limiting

## 11. **Testing Rate Limits**

### Load Testing
```python
import asyncio
import aiohttp
import time

async def test_rate_limit(url, requests_per_second, duration):
    connector = aiohttp.TCPConnector(limit=100)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        start_time = time.time()
        results = {'success': 0, 'rate_limited': 0, 'errors': 0}
        
        while time.time() - start_time < duration:
            tasks = []
            for _ in range(requests_per_second):
                tasks.append(make_request(session, url, results))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(1)
        
        return results

async def make_request(session, url, results):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                results['success'] += 1
            elif response.status == 429:  # Too Many Requests
                results['rate_limited'] += 1
            else:
                results['errors'] += 1
    except Exception:
        results['errors'] += 1
```

## Summary

Rate limiting is essential for:
- **Security**: Preventing abuse and DoS attacks
- **Resource Management**: Ensuring fair usage
- **Service Quality**: Maintaining performance under load
- **Cost Control**: Managing API and infrastructure costs

Choose the appropriate algorithm based on your specific requirements:
- **Token Bucket**: Good for allowing bursts
- **Sliding Window**: Most accurate for strict limits
- **Fixed Window**: Simple and memory efficient
- **Leaky Bucket**: Best for smoothing traffic

Always implement proper monitoring, graceful degradation, and clear error responses for the best user experience.
