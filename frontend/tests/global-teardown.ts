import * as fs from 'fs';
import * as path from 'path';

const TEST_STATE_FILE = path.join(__dirname, '.test-state.json');

async function globalTeardown() {
  console.log('🧹 Global Teardown: Cleaning up test environment...');

  try {
    // Clean up test state file
    if (fs.existsSync(TEST_STATE_FILE)) {
      fs.unlinkSync(TEST_STATE_FILE);
      console.log('✅ Test state file removed');
    }

    console.log('✨ Global teardown completed successfully!');
  } catch (error) {
    console.error('⚠️ Global teardown warning:', error);
  }
}

export default globalTeardown;
