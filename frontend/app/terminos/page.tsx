import type { Metadata } from "next"
import LegalPageLayout, { type LegalSection } from "@/components/legal/legal-page"
import { fetchLegalDocument } from "@/lib/legal"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Términos y Condiciones — WMS",
  description: "Términos y Condiciones de uso del sistema WMS de gestión de almacén e inventario.",
}

const SECTIONS: LegalSection[] = [
  {
    title: "1. Objeto y aceptación",
    paragraphs: [
      "Estos Términos y Condiciones regulan el acceso y uso del software WMS de gestión de almacén e inventario (en adelante, «el Software»). Al acceder a la aplicación, iniciar sesión o utilizarla, usted acepta íntegramente estas condiciones.",
      "Si utiliza el Software en nombre de una organización, declara disponer de facultades suficientes para vincularla y aceptar estas condiciones en su nombre.",
    ],
  },
  {
    title: "2. Licencia de uso (MIT)",
    paragraphs: [
      "El Software se distribuye bajo licencia MIT. Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia del Software y de los archivos de documentación asociados, para utilizarlo, copiarlo, modificarlo, fusionarlo, publicarlo, distribuirlo, sublicenciarlo y/o venderlo, con sujeción a las condiciones de la licencia MIT.",
      "El aviso de copyright y el texto de la licencia deberán incluirse en todas las copias o partes sustanciales del Software.",
      "El Software se entrega «TAL CUAL» («AS IS»), SIN GARANTÍA DE NINGÚN TIPO, expresa o implícita, incluidas, entre otras, las garantías de comerciabilidad, idoneidad para un fin concreto y no infracción.",
    ],
  },
  {
    title: "3. Responsabilidad del cliente",
    bullets: [
      "El cliente es el único responsable de la configuración, el despliegue, la administración y el uso del Software en su organización.",
      "El cliente es responsable de la exactitud e integridad de los datos que introduce (artículos, stock, lotes, series, inventarios, usuarios y logs).",
      "El cliente debe implantar sus propias políticas de copias de seguridad, continuidad del negocio, control de accesos y gestión de incidentes.",
      "Cuando el Software se utilice en entornos regulados (por ejemplo, GxP, dispositivos médicos, alimentación, farmacia o productos sanitarios), el cliente es responsable de la validación del sistema, de los procedimientos de calidad y del cumplimiento de la normativa aplicable.",
      "El cliente es responsable del cumplimiento del Reglamento General de Protección de Datos (RGPD) y de la Ley Orgánica de Protección de Datos y Garantía de los Derechos Digitales (LOPDGDD) respecto de los datos personales tratados mediante el Software.",
    ],
  },
  {
    title: "4. Uso permitido",
    paragraphs: [
      "El usuario se compromete a utilizar el Software conforme a la ley, a estas condiciones y a las instrucciones de su organización. Queda prohibido intentar acceder a datos de otras empresas, eludir los controles de acceso, introducir código malicioso o realizar actividades que comprometan la disponibilidad, integridad o confidencialidad del sistema.",
    ],
  },
  {
    title: "5. Multitenencia y datos",
    paragraphs: [
      "El Software incorpora aislamiento multitenencia por empresa. No obstante, el cliente es responsable de asignar correctamente usuarios, roles y permisos, y de revisar periódicamente los accesos.",
      "Los registros de auditoría se conservan para fines de trazabilidad y seguridad. Su plazo de conservación debe ser definido por el cliente conforme a sus obligaciones legales y sectoriales.",
    ],
  },
  {
    title: "6. Limitación de responsabilidad",
    paragraphs: [
      "En la máxima medida permitida por la ley aplicable, los autores y titulares de los derechos del Software no serán responsables de ningún daño directo, indirecto, incidental, especial, ejemplar o consecuente, ni de la pérdida de datos, de beneficios o de negocio, derivados del uso o de la imposibilidad de uso del Software.",
      "Nada en estos Términos excluye o limita la responsabilidad que no pueda excluirse o limitarse conforme a la normativa imperativa aplicable, incluida la normativa de consumo o de protección de datos.",
    ],
  },
  {
    title: "7. Modificaciones y legislación aplicable",
    paragraphs: [
      "Estos Términos podrán actualizarse para reflejar cambios funcionales, legales o de seguridad. La versión vigente será la publicada en esta página.",
      "Estos Términos se rigen por la legislación española y de la Unión Europea que resulte aplicable. Cualquier controversia se someterá a los juzgados y tribunales competentes conforme a la ley aplicable, sin perjuicio de los derechos imperativos que asistan al consumidor.",
    ],
  },
  {
    title: "8. Contacto",
    paragraphs: [
      "Para cualquier consulta relacionada con estos Términos y Condiciones, diríjase al responsable de su organización que administra esta instancia del Software.",
    ],
  },
]

export default async function TerminosPage() {
  const remote = await fetchLegalDocument("terminos")

  return (
    <LegalPageLayout
      title="Términos y Condiciones de Uso"
      subtitle="Condiciones aplicables al uso del sistema WMS de gestión de almacén e inventario."
      updatedAt="11 de noviembre de 2026"
      remoteSummary={remote ? { contenido: remote.contenido, version: remote.version } : null}
      sections={SECTIONS}
    />
  )
}
