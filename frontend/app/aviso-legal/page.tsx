import type { Metadata } from "next"
import LegalPageLayout, { type LegalSection } from "@/components/legal/legal-page"
import { fetchLegalDocument } from "@/lib/legal"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Aviso Legal — WMS",
  description: "Aviso legal, licencia MIT y limitación de responsabilidad del sistema WMS.",
}

const SECTIONS: LegalSection[] = [
  {
    title: "1. Información general",
    paragraphs: [
      "Este Aviso Legal regula el acceso y uso de la aplicación WMS de gestión de almacén e inventario. La instancia que está consultando es operada por la organización que la ha desplegado; los datos de identificación, contacto y registro que resulten exigibles deben ser publicados por dicha organización.",
      "El Software es un proyecto distribuido como código abierto bajo licencia MIT. El repositorio y la licencia constituyen la referencia para los términos de uso del código.",
    ],
  },
  {
    title: "2. Objeto",
    paragraphs: [
      "La aplicación tiene por objeto la gestión de almacén e inventario: maestros de artículos, ubicaciones, stock, trazabilidad por lote y número de serie, inventarios físicos, ajustes, alertas, informes y auditoría.",
    ],
  },
  {
    title: "3. Propiedad intelectual y licencia",
    paragraphs: [
      "El Software se distribuye bajo licencia MIT. Se permite su uso, copia, modificación y distribución conforme a los términos de dicha licencia, conservando el aviso de copyright y el texto de la licencia.",
      "Las marcas, nombres comerciales y contenidos aportados por el cliente son titularidad de sus respectivos propietarios.",
    ],
  },
  {
    title: "4. Exclusión de garantías",
    paragraphs: [
      "El Software se proporciona «TAL CUAL» y «SEGÚN DISPONIBILIDAD», sin garantías de ningún tipo, expresas o implícitas, incluidas las de comerciabilidad, idoneidad para un fin concreto, exactitud o no infracción. No se garantiza que el funcionamiento sea ininterrumpido o libre de errores.",
    ],
  },
  {
    title: "5. Limitación de responsabilidad",
    paragraphs: [
      "En la máxima medida permitida por la ley, los autores y contribuidores del Software no serán responsables de daños directos o indirectos, pérdida de datos, lucro cesante, interrupción de la actividad o cualquier perjuicio derivado del uso del Software o de la imposibilidad de utilizarlo.",
      "El cliente asume la responsabilidad de validar el sistema para su uso previsto, de realizar copias de seguridad, de gestionar accesos y de cumplir la normativa que le sea aplicable, incluida la relativa a productos sanitarios, alimentación, farmacia y demás entornos GxP, así como el RGPD y la LOPDGDD.",
    ],
  },
  {
    title: "6. Enlaces externos",
    paragraphs: [
      "La aplicación puede incluir enlaces a sitios de terceros. No se controla ni se asume responsabilidad alguna sobre sus contenidos, políticas o prácticas de privacidad.",
    ],
  },
  {
    title: "7. Legislación aplicable y jurisdicción",
    paragraphs: [
      "Este Aviso Legal se rige por la legislación española y de la Unión Europea aplicable. Cualquier controversia se someterá a los juzgados y tribunales competentes conforme a la normativa vigente, respetando en todo caso los derechos imperativos reconocidos a consumidores y usuarios.",
    ],
  },
  {
    title: "8. Contacto",
    paragraphs: [
      "Para cuestiones relativas a esta instancia del Software, contacte con el administrador o responsable designado por la organización que la opera.",
    ],
  },
]

export default async function AvisoLegalPage() {
  const remote = await fetchLegalDocument("aviso-legal")

  return (
    <LegalPageLayout
      title="Aviso Legal"
      subtitle="Información legal, licencia MIT y limitación de responsabilidad."
      updatedAt="11 de noviembre de 2026"
      remoteSummary={remote ? { contenido: remote.contenido, version: remote.version } : null}
      sections={SECTIONS}
    />
  )
}
