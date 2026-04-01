import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const frontendDir = path.resolve(__dirname, '..')
const repoRoot = path.resolve(frontendDir, '..')

const version = fs.readFileSync(path.join(repoRoot, 'VERSION'), 'utf8').trim()

for (const fileName of ['package.json', 'package-lock.json']) {
  const filePath = path.join(frontendDir, fileName)
  const parsed = JSON.parse(fs.readFileSync(filePath, 'utf8'))
  parsed.version = version

  if (fileName === 'package-lock.json' && parsed.packages?.['']) {
    parsed.packages[''].version = version
  }

  fs.writeFileSync(filePath, `${JSON.stringify(parsed, null, 2)}\n`, 'utf8')
}

console.log(`Synced frontend version to ${version}`)
