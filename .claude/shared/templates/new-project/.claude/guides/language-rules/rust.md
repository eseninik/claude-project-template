# Rust Coding Rules

> Consolidated coding standards for Rust projects. Adapted from ECC rule packs.

## Style & Formatting

- **rustfmt** — mandatory
- **clippy** — all warnings, `#![deny(clippy::all)]`
- **Zero unsafe** unless absolutely necessary (and documented)
- **Ownership-first** thinking — borrow before clone

## Naming

| Entity | Convention | Example |
|--------|-----------|---------|
| Types/Traits | PascalCase | `UserService`, `Repository` |
| Functions/methods | snake_case | `get_by_id()`, `process_order()` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Modules | snake_case | `user_service` |
| Lifetime params | short lowercase | `'a`, `'ctx` |
| Type params | single uppercase | `T`, `E` |

## Patterns

### Repository Trait
```rust
pub trait OrderRepository: Send + Sync {
    fn find_by_id(&self, id: u64) -> Result<Option<Order>, StorageError>;
    fn save(&self, order: &Order) -> Result<Order, StorageError>;
    fn delete(&self, id: u64) -> Result<(), StorageError>;
}
```

### Newtype for Type Safety
```rust
struct UserId(u64);
struct OrderId(u64);
// Can't accidentally swap at call sites
fn get_order(user: UserId, order: OrderId) -> Result<Order> { ... }
```

### Builder Pattern
```rust
pub struct ServerBuilder {
    port: u16,
    workers: usize,
}

impl ServerBuilder {
    pub fn new() -> Self { Self { port: 8080, workers: 4 } }
    pub fn port(mut self, port: u16) -> Self { self.port = port; self }
    pub fn build(self) -> Server { Server { port: self.port, workers: self.workers } }
}
```

## Error Handling

```rust
// thiserror for library errors
#[derive(Debug, thiserror::Error)]
enum AppError {
    #[error("user {0} not found")]
    NotFound(u64),
    #[error("database error: {0}")]
    Database(#[from] sqlx::Error),
}

// anyhow for application code
fn process() -> anyhow::Result<()> {
    let user = repo.find(id).context("loading user")?;
    Ok(())
}
```

## Testing

- **Built-in:** `#[cfg(test)]` module
- **Integration tests** in `tests/` directory
- **Assertions:** `assert_eq!`, `assert!(matches!(...))`, `assert!(result.is_err())`
- **Coverage:** `cargo tarpaulin` or `cargo llvm-cov`
- **Mocking:** trait objects or mockall crate

## Concurrency

- **Prefer `tokio` async** for I/O-bound work
- **`rayon`** for CPU-bound parallelism
- **Channels** (`tokio::sync::mpsc`) for inter-task communication
- **Never** share mutable state without `Mutex`/`RwLock`
- **`Arc<T>`** for shared ownership across tasks

## Security

- **No `unsafe`** without documented safety invariants
- **Always** use parameterized SQL (`sqlx::query!`)
- **Validate** all external input before processing
- **Use `secrecy::Secret<T>`** for sensitive data (prevents accidental logging)

## Logging

```rust
use tracing::{info, error, instrument};

#[instrument(skip(repo))]
async fn create_user(repo: &dyn UserRepo, req: CreateUserReq) -> Result<User> {
    info!(email = %req.email, "creating user");
    let user = repo.create(&req).await?;
    info!(user_id = user.id, "user created");
    Ok(user)
}
```
