import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://gttcqjglxmqwyrmgquax.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd0dGNxamdseG1xd3lybWdxdWF4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyNzQ1NjcsImV4cCI6MjA4OTg1MDU2N30.2J_wzy8SZHSgrFPzsNy7CB1oXNifCi1Yy0UFkHSNbHI'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
