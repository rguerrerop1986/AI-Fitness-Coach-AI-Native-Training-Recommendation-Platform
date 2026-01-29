import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { useTranslation } from 'react-i18next'
import { toast } from 'react-hot-toast'
import { Dumbbell, Moon, Sun } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const { t } = useTranslation()

  const loginSchema = z.object({
    username: z.string().min(1, t('validation.required')),
    password: z.string().min(1, t('validation.required')),
  })

  type LoginForm = z.infer<typeof loginSchema>

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    try {
      await login(data.username, data.password)
      toast.success('Login successful!')
      navigate('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="absolute top-4 right-4">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          title={theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
        >
          {theme === 'dark' ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </button>
      </div>
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900">
            <Dumbbell className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-gray-100">
            {t('auth.loginTitle')}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            {t('auth.loginSubtitle')}
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="form-label">
                {t('auth.email')}
              </label>
              <input
                id="username"
                type="text"
                {...register('username')}
                className="input"
                placeholder={t('auth.email')}
              />
              {errors.username && (
                <p className="form-error">{errors.username.message}</p>
              )}
            </div>
            <div>
              <label htmlFor="password" className="form-label">
                {t('auth.password')}
              </label>
              <input
                id="password"
                type="password"
                {...register('password')}
                className="input"
                placeholder={t('auth.password')}
              />
              {errors.password && (
                <p className="form-error">{errors.password.message}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full"
            >
              {loading ? t('common.loading') : t('auth.loginButton')}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Demo credentials:
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              Coach: coach / demo123
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500">
              Assistant: assistant / demo123
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}
