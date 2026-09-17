// 可以在 https://www.ibujian.cn/vue-plugin-hiprint/ 在线设计好之后，复制json
// 但建议是拉取源码 https://gitee.com/CcSimple/vue-plugin-hiprint 然后本地跑项目

import { hiprint } from "vue-plugin-hiprint";
// 模板
const template = {
  panels: [
    {
      index: 0,
      name: 1,
      height: 297,
      width: 210,
      paperHeader: 39,
      paperFooter: 808.5,
      printElements: [
        {
          options: {
            left: 216,
            top: 48,
            height: 17,
            width: 120,
            testData: "作者信息",
            fontSize: 16.5,
            fontWeight: "700",
            textAlign: "center",
            hideTitle: true,
            title: "作者信息",
            qid: "author",
            coordinateSync: false,
            widthHeightSync: false,
            qrCodeLevel: 0
          },
          printElementType: { title: "作者信息", type: "text" }
        },
        {
          options: {
            left: 28.5,
            top: 69,
            height: 9,
            width: 555,
            borderWidth: 0.75
          },
          printElementType: { title: "横线", type: "hline" }
        },
        {
          options: {
            left: 30,
            top: 78,
            height: 16,
            width: 200,
            field: "name",
            testData: "李四",
            fontSize: 12,
            fontWeight: "700",
            textAlign: "left",
            textContentVerticalAlign: "middle",
            title: "姓名",
            qid: "name",
            coordinateSync: false,
            widthHeightSync: false,
            qrCodeLevel: 0,
            right: 208.5,
            bottom: 94,
            vCenter: 148.5,
            hCenter: 86
          },
          printElementType: { title: "作者姓名", type: "text" }
        },
        {
          options: {
            left: 337.5,
            top: 108,
            height: 16,
            width: 200,
            field: "gender",
            testData: "性别",
            fontSize: 12,
            fontWeight: "700",
            textAlign: "left",
            textContentVerticalAlign: "middle",
            title: "性别",
            qid: "gender",
            coordinateSync: false,
            widthHeightSync: false,
            qrCodeLevel: 0,
            right: 333,
            bottom: 141.25,
            vCenter: 273,
            hCenter: 133.25
          },
          printElementType: { title: "性别", type: "text" }
        },
        {
          options: {
            left: 28.5,
            top: 108,
            height: 16,
            width: 200,
            field: "birth_date",
            testData: "出生日期",
            fontSize: 12,
            fontWeight: "700",
            textAlign: "left",
            textContentVerticalAlign: "middle",
            title: "出生日期",
            qid: "birth_date",
            coordinateSync: false,
            widthHeightSync: false,
            qrCodeLevel: 0,
            right: 426,
            bottom: 94,
            vCenter: 366,
            hCenter: 86
          },
          printElementType: { title: "出生日期", type: "text" }
        },
        {
          options: {
            left: 339,
            top: 79.5,
            height: 16,
            width: 200,
            field: "nationality",
            testData: "国籍",
            fontSize: 12,
            fontWeight: "700",
            textAlign: "left",
            textContentVerticalAlign: "middle",
            title: "国籍",
            qid: "nationality",
            coordinateSync: false,
            widthHeightSync: false,
            qrCodeLevel: 0,
            right: 450.75,
            bottom: 121,
            vCenter: 390.75,
            hCenter: 113
          },
          printElementType: { title: "国籍", type: "text" }
        },
        {
          options: {
            left: 25.5,
            top: 147,
            height: 69,
            width: 555,
            field: "biography",
            testData: "长文本分页/不分页测试",
            title: "简介",
            qid: "biography",
            right: 582,
            bottom: 215.25,
            vCenter: 304.5,
            hCenter: 180.75,
            coordinateSync: false,
            widthHeightSync: false,
            fontSize: 10.5
          },
          printElementType: { title: "简介", type: "longText" }
        },
        {
          options: {
            left: 25.5,
            top: 237,
            height: 9,
            width: 555,
            borderWidth: 0.75,
            right: 580.5,
            bottom: 245.25,
            vCenter: 303,
            hCenter: 240.75
          },
          printElementType: { title: "横线", type: "hline" }
        },
        {
          options: {
            left: 235.5,
            top: 256.5,
            height: 15,
            width: 120,
            testData: "著作",
            fontSize: 16.5,
            field: "headera",
            fontWeight: "700",
            textAlign: "center",
            hideTitle: true,
            title: "著作",
            qid: "headera",
            coordinateSync: false,
            widthHeightSync: false,
            qrCodeLevel: 0,
            right: 354.75,
            bottom: 270.75,
            vCenter: 294.75,
            hCenter: 263.25
          },
          printElementType: { title: "著作", type: "text" }
        },
        {
          options: {
            left: 37.5,
            top: 289.5,
            height: 54,
            width: 550,
            tableFooterRepeat: "last",
            fields: [
              { text: "书名", field: "name" },
              { text: "isbn", field: "isbn" },
              { text: "出版社", field: "publisher" },
              { text: "出版日期", field: "publication_date" },
              { text: "页数", field: "pages" },
              { text: "内容简介", field: "description" }
            ],
            field: "books",
            tableHeaderRepeat: "page",
            qid: "books",
            right: 587.5,
            bottom: 342.75,
            vCenter: 312.5,
            hCenter: 315.75,
            coordinateSync: false,
            widthHeightSync: false,
            fontSize: 10.5,
            tableBodyRowBorder: "border",
            tableBodyCellBorder: "border",
            columns: [
              [
                {
                  width: 86.77517560240966,
                  title: "书名",
                  field: "name",
                  checked: true,
                  columnId: "name",
                  fixed: false,
                  rowspan: 1,
                  colspan: 1,
                  align: "center"
                },
                {
                  width: 56.05338865461848,
                  title: "isbn",
                  field: "isbn",
                  checked: true,
                  columnId: "isbn",
                  fixed: false,
                  rowspan: 1,
                  colspan: 1,
                  align: "center"
                },
                {
                  width: 77.29176706827312,
                  title: "出版社",
                  field: "publisher",
                  checked: true,
                  columnId: "publisher",
                  fixed: false,
                  rowspan: 1,
                  colspan: 1,
                  align: "center"
                },
                {
                  width: 91.91154819277111,
                  title: "出版日期",
                  field: "publication_date",
                  checked: true,
                  columnId: "publication_date",
                  fixed: false,
                  rowspan: 1,
                  colspan: 1,
                  align: "center"
                },
                {
                  width: 53.02831024096385,
                  title: "页数",
                  field: "pages",
                  checked: true,
                  columnId: "pages",
                  fixed: false,
                  rowspan: 1,
                  colspan: 1,
                  align: "center"
                },
                {
                  width: 184.9398102409638,
                  title: "内容简介",
                  field: "description",
                  checked: true,
                  columnId: "description",
                  fixed: false,
                  rowspan: 1,
                  colspan: 1,
                  align: "center"
                }
              ]
            ]
          },
          printElementType: {
            title: "著作",
            type: "table",
            editable: true,
            columnDisplayEditable: true,
            columnDisplayIndexEditable: true,
            columnTitleEditable: true,
            columnResizable: true,
            columnAlignEditable: true,
            isEnableEditField: true,
            isEnableContextMenu: true,
            isEnableInsertRow: true,
            isEnableDeleteRow: true,
            isEnableInsertColumn: true,
            isEnableDeleteColumn: true,
            isEnableMergeCell: true
          }
        }
      ],
      paperNumberLeft: 270,
      paperNumberTop: 816,
      paperNumberContinue: true,
      watermarkOptions: {},
      panelLayoutOptions: {}
    }
  ]
};

// 初始化
hiprint.init();
const hiprintTemplate = new hiprint.PrintTemplate({
  template: template
});
export const print = (printData: object) => {
  hiprintTemplate.print(printData);
};
