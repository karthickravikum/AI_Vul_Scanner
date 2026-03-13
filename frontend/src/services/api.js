/**
 * services/api.js
 * ---------------
 * All HTTP communication with the Flask backend goes through here.
 * Using a centralised service means the base URL is configured in
 * one place, and every component gets consistent error handling.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,          // 60 s — scans can take a while
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Kick off a new scan.
 * @param {string} url - The target website URL to scan.
 * @returns {Promise<{scan_id, target, timestamp, total_scanned, vulnerability_count}>}
 */
export async function startScan(url) {
  const { data } = await client.post('/scan', { url })
  return data
}

/**
 * Fetch the full vulnerability report for a completed scan.
 * @param {string} scanId - UUID returned by startScan().
 * @returns {Promise<{scan_id, target, scan_timestamp, total_endpoints_scanned, vulnerabilities[]}>}
 */
export async function getReport(scanId) {
  const { data } = await client.get(`/report/${scanId}`)
  return data
}
