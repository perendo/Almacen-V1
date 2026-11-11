import type { Metadata } from "next"
import LegalPageLayout, { type LegalSection } from "@/components/legal/legal-page"
import { fetchLegalDocument } from "@/lib/legal"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Política de Privacidad — WMS",
  description:
    "Política de Privacidad del sistema WMS conforme al RGPD y la LOPDGDD (España/UE).",
}

const SECTIONS: LegalSection[] = [
  {
    title: "1. Marco normativo",
    paragraphs: [
      "Esta Política de Privacidad describe el tratamiento de datos personales en el sistema WMS conforme al Reglamento (UE) 2016/679, General de Protección de Datos (RGPD), y a la Ley Orgánica 3/2018, de Protección de Datos Personales y garantía de los derechos digitales (LOPDGDD).",
    ],
  },
  {
    title: "2. Roles: responsable y encargado del tratamiento",
    paragraphs: [
      "La organización que despliega y opera esta instancia del Software actúa como responsable del tratamiento de los datos personales que gestiona (usuarios, personal, proveedores y contactos).",
      "Los autores del Software no acceden a los datos alojados por el cliente salvo que exista un acuerdo específico de soporte o mantenimiento. En tal caso, actuarían como encargados del tratamiento y únicamente siguiendo las instrucciones documentadas del responsable.",
    ],
  },
  {
    title: "3. Datos tratados",
    bullets: [
      "Datos identificativos y de contacto de los usuarios: nombre completo, dirección de correo electrónico y empresa asignada.",
      "Credenciales de acceso: contraseñas almacenadas exclusivamente como hash bcrypt; nunca en texto plano.",
      "Datos de actividad y seguridad: fecha y hora de acceso, dirección IP, acciones realizadas, entidad afectada y valores anteriores y nuevos cuando proceda (logs de auditoría).",
      "Datos operativos del almacén: artículos, existencias, lotes, números de serie, inventarios y ajustes. Estos datos pueden estar vinculados a personas cuando así lo determine el cliente.",
    ],
  },
  {
    title: "4. Finalidades y bases jurídicas",
    bullets: [
      "Prestación del servicio y gestión de la relación contractual: base jurídica de ejecución de un contrato (art. 6.1.b RGPD).",
      "Seguridad de la información, prevención del fraude y trazabilidad: interés legítimo del responsable (art. 6.1.f RGPD), ponderado con los derechos de los interesados.",
      "Cumplimiento de obligaciones legales, incluidas las fiscales, contables y sectoriales: (art. 6.1.c RGPD).",
      "Comunicaciones no esenciales o finalidades adicionales: consentimiento del interesado (art. 6.1.a RGPD), revocable en cualquier momento.",
    ],
  },
  {
    title: "5. Conservación de los datos",
    paragraphs: [
      "Los datos se conservarán durante la relación contractual y, posteriormente, durante los plazos de prescripción legal aplicables. Los logs de auditoría y de seguridad se conservarán durante el periodo que defina el responsable en su política de conservación, atendiendo a sus obligaciones normativas y sectoriales.",
    ],
  },
  {
    title: "6. Destinatarios y transferencias internacionales",
    paragraphs: [
      "Con carácter general, no se comunican datos a terceros salvo obligación legal o cuando sea necesario para la prestación del servicio (por ejemplo, proveedores de infraestructura que actúen como encargados).",
      "Si se producen transferencias fuera del Espacio Económico Europeo, el responsable deberá garantizar un nivel de protección adecuado mediante decisión de adecuación, cláusulas contractuales tipo u otras garantías previstas en el RGPD.",
    ],
  },
  {
    title: "7. Derechos de los interesados",
    paragraphs: [
      "Las personas interesadas pueden ejercer los derechos de acceso, rectificación, supresión, limitación del tratamiento, portabilidad y oposición, así como retirar su consentimiento cuando el tratamiento se base en él.",
      "Para ejercer estos derechos, diríjase al responsable del tratamiento de su organización. Si considera que el tratamiento no cumple la normativa, puede presentar una reclamación ante la Agencia Española de Protección de Datos (AEPD) o la autoridad de control de su Estado miembro.",
    ],
  },
  {
    title: "8. Medidas de seguridad",
    bullets: [
      "Autenticación mediante tokens JWT de acceso y refresco, con revocación de tokens y cierre de sesión.",
      "Contraseñas almacenadas con bcrypt y políticas de cambio de contraseña.",
      "Control de acceso basado en roles (RBAC) y aislamiento multitenencia por empresa.",
      "Registro de auditoría de las operaciones sensibles.",
      "Recomendación de despliegue sobre HTTPS/TLS y de aplicación de copias de seguridad cifradas.",
    ],
  },
  {
    title: "9. Cookies y almacenamiento local",
    paragraphs: [
      "La aplicación utiliza almacenamiento local del navegador para conservar el token de sesión y la preferencia de tema, así como una cookie técnica necesaria para la protección de rutas privadas. No se utilizan cookies publicitarias ni de perfilado.",
    ],
  },
  {
    title: "10. Menores de edad",
    paragraphs: [
      "El Software está dirigido a profesionales y no se destina a menores de 14 años. El responsable debe abstenerse de introducir datos de menores sin la base jurídica y las garantías exigidas por la normativa aplicable.",
    ],
  },
  {
    title: "11. Cambios en esta política",
    paragraphs: [
      "El responsable podrá actualizar esta Política de Privacidad para adaptarla a cambios normativos o funcionales. La versión vigente será la publicada en esta página.",
    ],
  },
]

export default async function PrivacidadPage() {
  const remote = await fetchLegalDocument("privacidad")

  return (
    <LegalPageLayout
      title="Política de Privacidad"
      subtitle="Tratamiento de datos personales conforme al RGPD y la LOPDGDD (España/UE)."
      updatedAt="11 de noviembre de 2026"
      remoteSummary={remote ? { contenido: remote.contenido, version: remote.version } : null}
      sections={SECTIONS}
    />
  )
}
