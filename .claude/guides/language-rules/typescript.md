# TypeScript Coding Rules

> Consolidated coding standards for TypeScript/JavaScript projects. Adapted from ECC rule packs.

## Style & Formatting

- **Strict TypeScript** — `strict: true` in tsconfig.json, no `any`
- **Tooling:** ESLint + Prettier, biome as alternative
- **Immutable by default:** `const`, `readonly`, `as const`, `Object.freeze()`
- **Functional style preferred** — pure functions, array methods over loops

## Naming

| Entity | Convention | Example |
|--------|-----------|---------|
| Variables/functions | camelCase | `userName`, `getUserById()` |
| Classes/interfaces | PascalCase | `UserService`, `ApiResponse` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Type parameters | Single uppercase | `T`, `K`, `V` |
| Files | kebab-case | `user-service.ts` |
| React components | PascalCase file | `UserCard.tsx` |

## Patterns

### API Response Type
```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: { code: string; message: string }
  pagination?: { total: number; page: number; limit: number }
}
```

### Repository Pattern
```typescript
interface Repository<T> {
  findAll(filters?: Filters): Promise<T[]>
  findById(id: string): Promise<T | null>
  create(data: CreateDto): Promise<T>
  update(id: string, data: UpdateDto): Promise<T>
  delete(id: string): Promise<void>
}
```

### Custom Hooks
```typescript
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}
```

## Testing

- **Framework:** vitest (preferred) or jest
- **E2E:** Playwright
- **Coverage:** minimum 80%
- **Pattern:** Arrange-Act-Assert, one assertion per test
- **Mocking:** `vi.mock()` / `jest.mock()`, prefer dependency injection

## Error Handling

```typescript
// Custom error classes
class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
  ) {
    super(message)
    this.name = 'AppError'
  }
}

// Zod validation at boundaries
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
})
```

## Security

- **Never** `eval()`, `innerHTML`, or `dangerouslySetInnerHTML` with user input
- **Always** validate with Zod at API boundaries
- **Always** parameterized queries (Prisma, Drizzle, Kysely)
- **Never** expose stack traces in production error responses
- **Always** `helmet()` middleware for Express, CSP headers

## Logging

```typescript
import pino from 'pino'
const logger = pino({ name: 'user-service' })

async function createUser(data: CreateUserDto): Promise<User> {
  logger.info({ action: 'createUser.start', email: data.email })
  const user = await repo.create(data)
  logger.info({ action: 'createUser.done', userId: user.id })
  return user
}
```
