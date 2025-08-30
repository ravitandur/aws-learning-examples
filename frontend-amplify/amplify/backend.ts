import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource.js';

export const backend = defineBackend({
  auth,
});