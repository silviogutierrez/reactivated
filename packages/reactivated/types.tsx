export interface FormFieldType<Widget> {
    name: string;
    label: string;
    help_text: string;
    widget: Widget;
}
