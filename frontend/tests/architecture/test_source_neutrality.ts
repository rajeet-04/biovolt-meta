import packageJson from '../../package.json'
import { describe, expect, it } from 'vitest'

const prohibitedTokens = ['biovolt_simulator', 'biovolt-sim-', 'is_simulated', 'source_type']
const sourceFiles = import.meta.glob('../../src/**/*', {
  eager: true,
  import: 'default',
  query: '?raw',
})

describe('frontend source neutrality', () => {
  it('does not couple source code to simulator-specific concepts', () => {
    const violations = Object.entries(sourceFiles).flatMap(([path, text]) => {
      if (typeof text !== 'string') {
        throw new TypeError(`Expected raw source text for ${path}`)
      }

      return prohibitedTokens
        .filter((token) => text.includes(token))
        .map((token) => `${path}: contains ${token}`)
    })

    expect(violations).toEqual([])
  })

  it('does not list a simulator package in frontend dependencies', () => {
    const dependencySections = [
      'dependencies',
      'devDependencies',
      'optionalDependencies',
      'peerDependencies',
    ]
    const dependencyNames = dependencySections.flatMap((section) => {
      const dependencies = packageJson[section as keyof typeof packageJson]
      return dependencies && typeof dependencies === 'object' ? Object.keys(dependencies) : []
    })

    expect(dependencyNames.some((name) => name.toLowerCase().includes('simulator'))).toBe(false)
  })
})
