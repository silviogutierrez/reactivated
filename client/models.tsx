import {WidgetType} from './components/Widget';
import {FieldType, FormViewProps} from '../exports';

declare module './exports' {
    interface FieldType {
        widget: WidgetType;
    }
}

export * from './exports';
