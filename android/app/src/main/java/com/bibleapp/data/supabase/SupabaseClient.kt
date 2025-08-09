package com.bibleapp.data.supabase

import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.realtime.Realtime
import io.github.jan.supabase.auth.Auth

object SupabaseClient {
    val client = createSupabaseClient(
        supabaseUrl = "https://fqmmqmojvafquunkovmv.supabase.co",
        supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZxbW1xbW9qdmFmcXV1bmtvdm12Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTQzNDYsImV4cCI6MjA2ODY3MDM0Nn0.vOiHdmk9hFKEo5J-m-V3O1qtEB7qUZCE7RnykIXefWs"
    ) {
        install(Postgrest)
        install(Realtime)
        install(Auth)
    }
}