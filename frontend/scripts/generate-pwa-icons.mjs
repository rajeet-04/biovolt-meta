import { mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import sharp from 'sharp'

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const markPath = resolve(frontendRoot, 'public/biovolt-mark.svg')
const iconsPath = resolve(frontendRoot, 'public/icons')

await mkdir(iconsPath, { recursive: true })

for (const size of [192, 512]) {
  await sharp(markPath).resize(size, size).png().toFile(resolve(iconsPath, `pwa-${size}x${size}.png`))
}

await sharp(markPath)
  .resize(512, 512, { fit: 'contain', background: '#0c100e' })
  .png()
  .toFile(resolve(iconsPath, 'pwa-maskable-512x512.png'))
