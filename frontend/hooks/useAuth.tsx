"use client"

// Punto unico de verdad para el contexto de autenticacion.
// El provider y el hook viven en "@/components/auth-provider"; este archivo
// solo los reexporta para evitar dos instancias distintas del contexto
// (lo que provocaba "useAuth must be used within an AuthProvider").
export { AuthProvider, useAuth } from "@/components/auth-provider"
