import { ref } from "vue";
import { SolarDay } from "tyme4ts";

const day = ref<Date>();

export function useSelectDay() {
  // 实现 公历 方法
  const getSolar = () => {
    const date = day?.value || new Date();
    return SolarDay.fromYmd(
      date.getFullYear(),
      date.getMonth() + 1,
      date.getDate()
    );
  };
  // 实现 农历 方法
  const getLunar = () => {
    const solar = getSolar();
    return solar.getLunarDay();
  };
  // 实现 星期 方法
  const getWeekDay = () => {
    const solar = getSolar();
    return `星期${solar.getWeek()}`;
  };

  // 实现 农历月日 方法
  const getLunarMD = () => {
    const lunar = getLunar();
    return `${lunar.getLunarMonth().getName()}${lunar.getName()}`;
  };
  // 实现 农历信息 方法
  const getSolarInfo = () => {
    const solar = getSolar();
    // 干支日
    const d = solar.getSixtyCycleDay();
    const y = d.getYear().getName();
    const m = d.getMonth().getName();
    const zodiac = d.getYear().getEarthBranch().getZodiac().getName();
    return `${y}【${zodiac}】年 ${m}月 ${d.getName()}`;
  };
  const getGoodThings = () => {
    const lunar = getLunar();
    // 宜：嫁娶, 祭祀, 理发
    return lunar.getRecommends().toLocaleString();
  };
  const getBadThings = () => {
    const lunar = getLunar();
    // 忌：破土, 出行, 栽种
    return lunar.getAvoids().toLocaleString();
  };
  return {
    day,
    getSolar,
    getLunar,
    getWeekDay,
    getLunarMD,
    getSolarInfo,
    getGoodThings,
    getBadThings
  };
}
