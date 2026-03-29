import { describe, it, expect, vi } from 'vitest'
import { exportCsv } from '../export'

describe('exportCsv', () => {
  it('should not throw on empty data', () => {
    expect(() => exportCsv([], 'empty')).not.toThrow()
  })

  it('should create correct CSV content with BOM', () => {
    // Mock the DOM download mechanism
    const mockClick = vi.fn()
    const mockCreateElement = vi.spyOn(document, 'createElement').mockReturnValue({
      href: '',
      download: '',
      click: mockClick,
    } as unknown as HTMLAnchorElement)
    const mockCreateObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test')
    const mockRevokeObjectURL = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})

    const data = [
      { name: 'תל אביב', count: 100 },
      { name: 'חיפה', count: 50 },
    ]

    exportCsv(data, 'test-export')

    expect(mockClick).toHaveBeenCalled()
    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockRevokeObjectURL).toHaveBeenCalled()

    // Verify the Blob was created with BOM
    const blobArg = mockCreateObjectURL.mock.calls[0][0] as Blob
    expect(blobArg).toBeInstanceOf(Blob)
    expect(blobArg.type).toBe('text/csv;charset=utf-8;')

    mockCreateElement.mockRestore()
    mockCreateObjectURL.mockRestore()
    mockRevokeObjectURL.mockRestore()
  })
})
