import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('App', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<App />)
    
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders health data on successful fetch', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        service: 'atlas-forge-145-alan-vo',
        version: '1.0.0'
      })
    })
    
    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('Service Health')).toBeInTheDocument()
    })
    
    expect(screen.getByText('ok')).toBeInTheDocument()
    expect(screen.getByText('atlas-forge-145-alan-vo')).toBeInTheDocument()
    expect(screen.getByText('1.0.0')).toBeInTheDocument()
  })

  it('renders error state on fetch failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))
    
    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  it('renders features list', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        service: 'atlas-forge-145-alan-vo',
        version: '1.0.0'
      })
    })
    
    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('Features')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Bounded media range responses (fixes connection starvation)')).toBeInTheDocument()
    expect(screen.getByText('OIDC authentication with Keycloak')).toBeInTheDocument()
    expect(screen.getByText('LLM provider adapters')).toBeInTheDocument()
    expect(screen.getByText('Video composition & rendering')).toBeInTheDocument()
  })
})
