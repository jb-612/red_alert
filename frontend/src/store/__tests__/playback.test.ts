import { describe, it, expect, beforeEach } from 'vitest'
import { usePlaybackStore } from '../playback'

describe('usePlaybackStore', () => {
  beforeEach(() => {
    usePlaybackStore.getState().reset()
  })

  it('should start with playing false', () => {
    expect(usePlaybackStore.getState().playing).toBe(false)
  })

  it('should play and pause', () => {
    usePlaybackStore.getState().play()
    expect(usePlaybackStore.getState().playing).toBe(true)

    usePlaybackStore.getState().pause()
    expect(usePlaybackStore.getState().playing).toBe(false)
  })

  it('should set speed', () => {
    usePlaybackStore.getState().setSpeed(5)
    expect(usePlaybackStore.getState().speed).toBe(5)
  })

  it('should set dates and reset index', () => {
    usePlaybackStore.getState().setDates(['2024-01-01', '2024-01-02', '2024-01-03'])
    expect(usePlaybackStore.getState().dates).toHaveLength(3)
    expect(usePlaybackStore.getState().currentIndex).toBe(0)
  })

  it('should tick through frames', () => {
    usePlaybackStore.getState().setDates(['2024-01-01', '2024-01-02', '2024-01-03'])
    usePlaybackStore.getState().tick()
    expect(usePlaybackStore.getState().currentIndex).toBe(1)
    usePlaybackStore.getState().tick()
    expect(usePlaybackStore.getState().currentIndex).toBe(2)
  })

  it('should wrap around to 0 and stop at end', () => {
    usePlaybackStore.getState().setDates(['2024-01-01', '2024-01-02'])
    usePlaybackStore.getState().play()
    usePlaybackStore.getState().tick() // 0 -> 1
    usePlaybackStore.getState().tick() // 1 -> 0, stops playing
    expect(usePlaybackStore.getState().currentIndex).toBe(0)
    expect(usePlaybackStore.getState().playing).toBe(false)
  })

  it('should seek to specific index', () => {
    usePlaybackStore.getState().setDates(['2024-01-01', '2024-01-02', '2024-01-03'])
    usePlaybackStore.getState().seekTo(2)
    expect(usePlaybackStore.getState().currentIndex).toBe(2)
  })

  it('should add and retrieve geo frames', () => {
    const geoData = [{ location_name: 'תל אביב', lat: 32.08, lng: 34.78, count: 5 }]
    usePlaybackStore.getState().addFrame('2024-01-01', geoData)
    expect(usePlaybackStore.getState().geoFrames.get('2024-01-01')).toEqual(geoData)
  })

  it('should reset all state', () => {
    usePlaybackStore.getState().setDates(['2024-01-01'])
    usePlaybackStore.getState().play()
    usePlaybackStore.getState().reset()
    expect(usePlaybackStore.getState().playing).toBe(false)
    expect(usePlaybackStore.getState().dates).toHaveLength(0)
    expect(usePlaybackStore.getState().currentIndex).toBe(0)
  })
})
