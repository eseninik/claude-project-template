# Go Coding Rules

> Consolidated coding standards for Go projects. Adapted from ECC rule packs.

## Style & Formatting

- **gofmt/goimports** — mandatory, no exceptions
- **golangci-lint** — comprehensive linting
- **Effective Go** + Go Code Review Comments as reference
- **Small interfaces** — define where used, not where implemented

## Naming

| Entity | Convention | Example |
|--------|-----------|---------|
| Exported | PascalCase | `UserService`, `GetByID()` |
| Unexported | camelCase | `userRepo`, `processOrder()` |
| Packages | short, lowercase, no underscores | `user`, `auth`, `httputil` |
| Interfaces | -er suffix for single method | `Reader`, `Writer`, `Storer` |
| Acronyms | ALL CAPS | `HTTPClient`, `userID` |

## Patterns

### Functional Options
```go
type Option func(*Server)

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func NewServer(opts ...Option) *Server {
    s := &Server{port: 8080}
    for _, opt := range opts { opt(s) }
    return s
}
```

### Constructor Injection
```go
func NewUserService(repo UserRepository, logger *slog.Logger) *UserService {
    return &UserService{repo: repo, logger: logger}
}
```

### Error Wrapping
```go
if err != nil {
    return fmt.Errorf("create user %s: %w", name, err)
}
```

## Error Handling

- **Always** check errors — never `_` on error returns
- **Wrap** errors with context: `fmt.Errorf("context: %w", err)`
- **Custom errors:** `errors.New()` or custom types implementing `error`
- **Sentinel errors:** `var ErrNotFound = errors.New("not found")`
- **Check with** `errors.Is()` and `errors.As()`, not string matching

## Testing

- **Built-in:** `testing` package
- **Table-driven tests** as default pattern
- **Subtests:** `t.Run("case name", func(t *testing.T) {...})`
- **Coverage:** `go test -cover ./...`
- **Mocking:** interfaces + test doubles (avoid heavy mock libs)

## Concurrency

```go
// Always use context for cancellation
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

// errgroup for parallel work
g, ctx := errgroup.WithContext(ctx)
g.Go(func() error { return fetchUsers(ctx) })
g.Go(func() error { return fetchOrders(ctx) })
if err := g.Wait(); err != nil { ... }
```

## Security

- **Always** use `html/template` (auto-escapes), never `text/template` for HTML
- **Always** parameterized SQL (`db.Query("SELECT ... WHERE id = $1", id)`)
- **Never** embed secrets in source — use env vars
- **Always** validate input at handler boundaries

## Logging

```go
logger := slog.Default()

func (s *UserService) CreateUser(ctx context.Context, req CreateUserReq) (*User, error) {
    logger.InfoContext(ctx, "action", "createUser.start", "email", req.Email)
    user, err := s.repo.Create(ctx, req)
    if err != nil {
        logger.ErrorContext(ctx, "action", "createUser.error", "error", err)
        return nil, fmt.Errorf("create user: %w", err)
    }
    logger.InfoContext(ctx, "action", "createUser.done", "userID", user.ID)
    return user, nil
}
```
