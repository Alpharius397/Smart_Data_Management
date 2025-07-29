export type JsTypesString = 'number' | 'string' | 'object'

export type JsTypes = number | string | object | null

export type HeaderType = {
    university: string,
    institute: string,
    branch: string,
}

export type RowData = {
    column: string,
    value: string
}

export type SubjectData = {
    subject: string
    value: string
    maxValue: string | number
}

export type SemData = {
    semester: string,
    subjects: Array<SubjectData>
}