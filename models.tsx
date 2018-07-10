import {WidgetType} from './components/Widget';
import {FieldType, FormViewProps} from './exports';

declare module './interfaces' {
    interface FieldType {
        widget: WidgetType;
    }
}

export * from './interfaces';
